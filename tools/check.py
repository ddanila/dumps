#!/usr/bin/env python3
"""Repository consistency checks for the ROM dump collection.

Run from anywhere:  python3 tools/check.py
Exits non-zero if any check fails. Uses only the Python standard library.

Checks:
  checksums  every *SHA256SUMS file verifies
  manifests  every sha256 in a manifest.json matches its named file (file /
             filename / image), or some file in the set if no name is given.
             Hashes of readers, public references and captures kept in local
             sessions (entries with "url" or "session") are not checked.
  schema     every set manifest uses dumps-manifest/1 and its "images" list
             matches exactly the dumps at the top of the set folder
  links      every relative Markdown link resolves
  paths      no personal absolute paths (/home/<user>/, /Users/<user>/) in
             Markdown or manifests; raw records under evidence/ are exempt
  summaries  no acquisition mechanics (read counts, reader names) in the root
             README or in the opening paragraph of a set README
  listed     every set (a folder with manifest.json) is reachable from a root
             README link to it or to one of its parent folders
"""
import hashlib
import json
import re
import subprocess
import sys
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOME_PATH = re.compile(r'/(?:home|Users)/[^/\s`"<]+/')
LINK = re.compile(r'\]\(([^)\s]+)\)')
ACQUISITION_WORDING = re.compile(
    r'\b(?:two|three|four|\d+)\s+(?:matching|identical|independent)\b[^.]*?\breads?\b'
    r'|\brepeat-read\b|\bT48\s+reads?\b|\bmatching\s+reads?\b|\bread\s+(?:twice|three times)\b',
    re.IGNORECASE)


def tracked_files():
    out = subprocess.run(['git', '-C', str(ROOT), 'ls-files', '--cached', '--others', '--exclude-standard'],
                         capture_output=True, text=True, check=True).stdout
    return [ROOT / line for line in out.splitlines() if (ROOT / line).is_file()]


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def rel(path):
    return str(path.relative_to(ROOT))


def check_checksums(files):
    errors = []
    for sums in (f for f in files if f.name.endswith('SHA256SUMS')):
        entries = []
        for line in sums.read_text().splitlines():
            if line.strip():
                digest, name = line.split(None, 1)
                entries.append((digest, name.lstrip('*')))
        # Paths are relative to the checksum file's folder, or to one subfolder
        # (e.g. CORE-SHA256SUMS describing a vendored emu8051/ directory).
        bases = [sums.parent] + sorted(p for p in sums.parent.iterdir() if p.is_dir())
        base = next((b for b in bases if all((b / n).is_file() for _, n in entries)), None)
        if base is None:
            errors.append(f'{rel(sums)}: listed files not found')
            continue
        for digest, name in entries:
            if sha256(base / name) != digest:
                errors.append(f'{rel(sums)}: {name} does not match')
    return errors


FILE_KEYS = ('file', 'filename', 'image')
# Hashes under these keys describe readers, public references or comparisons.
EXTERNAL_KEY = re.compile(r'reader|public|comparison|reference', re.IGNORECASE)
DOC_SUFFIXES = {'.md', '.json', '.txt', '.csv', '.tsv', '.log', '.py', '.c', '.h', '.sh', '.lua', '.asm', '.svg', '.jpg', '.png'}
_hash_cache = {}


def cached_sha256(path):
    if path not in _hash_cache:
        _hash_cache[path] = sha256(path)
    return _hash_cache[path]


def manifest_hashes(manifest):
    """Yield (named_file_or_None, sha256) for each hash entry in a manifest."""
    def walk(node, external):
        if isinstance(node, dict):
            if isinstance(node.get('sha256'), str):
                name = next((node[k] for k in FILE_KEYS if isinstance(node.get(k), str)), None)
                # Without a file name, a hash next to a URL or a local session path
                # describes something outside the repository.
                if name is not None or not (external or 'url' in node or 'session' in node):
                    yield name, node['sha256']
            for key, value in node.items():
                yield from walk(value, external or EXTERNAL_KEY.search(key) is not None)
        elif isinstance(node, list):
            for value in node:
                yield from walk(value, external)
    yield from walk(json.loads(manifest.read_text()), False)


def check_manifests(files):
    errors = []
    by_folder = {}
    for f in files:
        by_folder.setdefault(f.parent, []).append(f)
    for manifest in (f for f in files if f.name == 'manifest.json'):
        folder = manifest.parent
        in_tree = [f for f in files if folder in f.parents and f.suffix not in DOC_SUFFIXES]
        try:
            entries = list(manifest_hashes(manifest))
        except json.JSONDecodeError as e:
            errors.append(f'{rel(manifest)}: invalid JSON ({e})')
            continue
        tree_hashes = None
        for name, digest in entries:
            if name is not None:
                target = folder / name
                if not target.is_file():
                    errors.append(f'{rel(manifest)}: missing {name}')
                elif cached_sha256(target) != digest:
                    errors.append(f'{rel(manifest)}: {name} does not match')
            else:
                if tree_hashes is None:
                    tree_hashes = {cached_sha256(f) for f in in_tree}
                if digest not in tree_hashes:
                    errors.append(f'{rel(manifest)}: sha256 {digest[:12]}… matches no file in the set')
    return errors


def check_schema(files):
    """Set manifests use dumps-manifest/1, and "images" lists exactly the set's dumps."""
    sys.path.insert(0, str(ROOT / 'tools'))
    from manifest import SCHEMA, is_dump
    errors = []
    for d in set_dirs(files):
        manifest = d / 'manifest.json'
        m = json.loads(manifest.read_text())
        where = rel(manifest)
        if m.get('schema') != SCHEMA:
            errors.append(f'{where}: not {SCHEMA} (run tools/manifest.py {rel(d)})')
            continue
        missing = [k for k in ('title', 'status', 'images', 'details') if k not in m]
        if missing or m['status'] not in ('preserved', 'record-only'):
            errors.append(f'{where}: missing {missing} or bad status')
            continue
        listed = {}
        for image in m['images']:
            if not all(k in image for k in ('file', 'size', 'sha256', 'sha1', 'crc32')):
                errors.append(f'{where}: incomplete image entry {image.get("file")}')
                continue
            f = d / image['file']
            if not f.is_file():
                errors.append(f'{where}: image {image["file"]} missing')
            elif f.stat().st_size != image['size'] or cached_sha256(f) != image['sha256']:
                errors.append(f'{where}: image {image["file"]} does not match')
            listed[image['file']] = image
        on_disk = {p.name for p in d.iterdir() if is_dump(p)}
        if m['status'] == 'record-only' and m['images']:
            errors.append(f'{where}: record-only set lists images')
        if m['status'] == 'preserved':
            for name in sorted(on_disk - set(listed)):
                errors.append(f'{rel(d / name)}: dump not listed in manifest images')
            if not listed:
                errors.append(f'{where}: preserved set has no images')
    return errors


def markdown(files):
    return [f for f in files if f.suffix == '.md']


def check_links(files):
    errors = []
    for md in markdown(files):
        for target in LINK.findall(md.read_text(errors='replace')):
            if re.match(r'[a-z][a-z0-9+.-]*:', target, re.IGNORECASE) or target.startswith('#'):
                continue
            path = urllib.parse.unquote(target.split('#', 1)[0])
            if path and not (md.parent / path).exists():
                errors.append(f'{rel(md)}: broken link {target}')
    return errors


def check_paths(files):
    errors = []
    for f in files:
        if 'evidence' in f.relative_to(ROOT).parts:
            continue
        if f.suffix == '.md' or f.name == 'manifest.json':
            for n, line in enumerate(f.read_text(errors='replace').splitlines(), 1):
                if HOME_PATH.search(line):
                    errors.append(f'{rel(f)}:{n}: personal absolute path')
    return errors


def set_dirs(files):
    return sorted({f.parent for f in files if f.name == 'manifest.json'
                   and 'evidence' not in f.relative_to(ROOT).parts
                   and 'analysis' not in f.relative_to(ROOT).parts
                   and 'photos' not in f.relative_to(ROOT).parts})


def intro(text):
    # Title line plus everything before the first second-level heading.
    match = re.search(r'^## ', text, re.MULTILINE)
    return text[:match.start()] if match else text


def check_summaries(files):
    errors = []
    root_readme = ROOT / 'README.md'
    for n, line in enumerate(root_readme.read_text().splitlines(), 1):
        if ACQUISITION_WORDING.search(line):
            errors.append(f'README.md:{n}: acquisition detail in root summary')
    for d in set_dirs(files):
        readme = d / 'README.md'
        if readme.is_file():
            for line in intro(readme.read_text()).splitlines():
                if ACQUISITION_WORDING.search(line):
                    errors.append(f'{rel(readme)}: acquisition detail in opening paragraph: {line.strip()[:70]}')
    return errors


def check_listed(files):
    root_readme = ROOT / 'README.md'
    linked = set()
    for target in LINK.findall(root_readme.read_text()):
        if not re.match(r'[a-z]+:', target):
            linked.add((ROOT / urllib.parse.unquote(target.split('#', 1)[0])).resolve())
    errors = []
    for d in set_dirs(files):
        chain = [d.resolve(), *d.resolve().parents]
        # A link to the top-level maker folder alone does not count as listing.
        if not any(p in linked for p in chain if len(p.relative_to(ROOT).parts) >= 2 or p == d.resolve()):
            errors.append(f'{rel(d)}: set not linked from root README')
    return errors


CHECKS = [('checksums', check_checksums), ('manifests', check_manifests), ('schema', check_schema), ('links', check_links),
          ('paths', check_paths), ('summaries', check_summaries), ('listed', check_listed)]


def main():
    files = tracked_files()
    failed = 0
    for name, check in CHECKS:
        errors = check(files)
        print(f'{name:10} {"ok" if not errors else f"{len(errors)} problem(s)"}')
        for e in errors:
            print(f'  {e}')
        failed += len(errors)
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
