#!/usr/bin/env python3
"""Search cached reference ROMs for shared, nontrivial 16-byte fragments.

Usage: python3 compare_fragments.py /tmp/u2716-referencecheck
Archives require unrar for RAR; no reference binaries are published here.
"""
import collections
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import zipfile

rom = (Path(__file__).resolve().parent.parent / 'rom.bin').read_bytes()
needles = {rom[i:i+16]: i for i in range(len(rom)-15)
           if len(set(rom[i:i+16])) >= 6}
results = []


def compare(name, data):
    hits = [(needles[data[j:j+16]], j) for j in range(len(data)-15)
            if data[j:j+16] in needles]
    results.append({'reference': name, 'size': len(data),
                    'sha256': hashlib.sha256(data).hexdigest(),
                    'matching_windows': len(hits),
                    'common_displacements': collections.Counter(j-i for i, j in hits).most_common(3)})


def unpack(name, data, path=None):
    if zipfile.is_zipfile(io.BytesIO(data)):
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            for member in archive.infolist():
                if not member.is_dir():
                    unpack(name+'!'+member.filename, archive.read(member))
    elif data.startswith(b'Rar!') and path:
        names = subprocess.check_output(['unrar', 'lb', str(path)]).decode().splitlines()
        for member in names:
            result = subprocess.run(['unrar', 'p', '-inul', str(path), member], capture_output=True, check=True)
            unpack(name+'!'+member, result.stdout)
    elif not name.lower().endswith(('.txt', '.md', '.html', '.jpg', '.png', '.pdf')):
        compare(name, data)


for directory in sys.argv[1:]:
    for path in sorted(Path(directory).rglob('*')):
        if path.is_file() and path.suffix.lower() in ('.rom', '.bin', '.zip', '.rar'):
            unpack(str(path.relative_to(directory)), path.read_bytes(), path)
print(json.dumps({'target_sha256': hashlib.sha256(rom).hexdigest(),
                  'window_size': 16, 'minimum_distinct_byte_values': 6,
                  'comparisons': results}, indent=2))
