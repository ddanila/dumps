#!/usr/bin/env python3
"""Create or refresh a set's manifest.json in the dumps-manifest/1 layout.

    python3 tools/manifest.py SET_DIR [SET_DIR ...] [--record-only] [--title TITLE]

The canonical core is generated from the files on disk:

    {
      "schema": "dumps-manifest/1",
      "title":  first line of README.md (or --title),
      "status": "preserved" | "record-only",
      "images": [{"file", "size", "sha256", "sha1", "crc32"}, ...],
      "details": { free-form acquisition and identification record }
    }

`images` lists every dump at the top of the set folder: files that are not
documentation, scripts, logs, archives or dotfiles. `record-only` sets keep
their binaries in local sessions and have no images. A legacy manifest without
"schema" is moved unchanged into "details". An existing "details" object is
never modified.
"""
import argparse
import hashlib
import json
import zlib
from pathlib import Path

SCHEMA = 'dumps-manifest/1'
NOT_DUMPS = {'.md', '.json', '.txt', '.csv', '.tsv', '.log', '.py', '.c', '.h', '.sh', '.lua', '.asm',
             '.svg', '.jpg', '.png', '.zip', '.gz'}


def is_dump(path):
    return (path.is_file() and path.suffix.lower() not in NOT_DUMPS and not path.name.startswith('.')
            and not path.name.endswith('SHA256SUMS'))


def describe(path):
    data = path.read_bytes()
    return {'file': path.name, 'size': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
            'sha1': hashlib.sha1(data).hexdigest(), 'crc32': f'{zlib.crc32(data) & 0xffffffff:08x}'}


def title_of(folder):
    readme = folder / 'README.md'
    if readme.is_file():
        first = readme.read_text().splitlines()[0]
        return first.lstrip('#').strip()
    return folder.name


def build(folder, record_only=None, title=None):
    path = folder / 'manifest.json'
    old = json.loads(path.read_text()) if path.is_file() else {}
    details = old['details'] if old.get('schema') == SCHEMA else old
    dumps = [describe(p) for p in sorted(folder.iterdir()) if is_dump(p)]
    if record_only is None:
        record_only = old.get('status') == 'record-only' or not dumps
    images = [] if record_only else dumps
    manifest = {'schema': SCHEMA,
                'title': title or (old.get('title') if old.get('schema') == SCHEMA else None) or title_of(folder),
                'status': 'record-only' if record_only else 'preserved',
                'images': images,
                'details': details}
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('folders', nargs='+', type=Path)
    parser.add_argument('--record-only', action='store_true', default=None)
    parser.add_argument('--title')
    args = parser.parse_args()
    for folder in args.folders:
        m = build(folder, args.record_only, args.title)
        print(f'{folder}: {m["status"]}, {len(m["images"])} image(s)')


if __name__ == '__main__':
    main()
