#!/usr/bin/env python3
"""Read-only, checksum-verified string extraction from the two archived ROMs."""

import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
SHIFTED = re.compile(rb"\x0e([\x20-\x7e]{4,})\x0f([\x20-\x7e]*)")


def interleave(even, odd):
    if len(even) != len(odd):
        raise ValueError("ROM lengths differ")
    result = bytearray(2 * len(even))
    result[0::2] = even
    result[1::2] = odd
    return bytes(result)


def strings(data):
    for match in SHIFTED.finditer(data):
        russian = bytes(b | 0x80 if 0x60 <= b <= 0x7e else b
                        for b in match[1]).decode("koi8-r")
        yield match.start(1), russian + match[2].decode("ascii")


def main():
    manifest = json.loads((ROOT / "manifest.json").read_text())
    images = {}
    for chip in manifest["chips"]:
        data = (ROOT / chip["filename"]).read_bytes()
        if len(data) != chip["bytes"] or hashlib.sha256(data).hexdigest() != chip["sha256"]:
            raise ValueError(f"archived image checksum/size mismatch: {chip['filename']}")
        images[chip["label"]] = data
    good = interleave(images["01"], images["02"])
    reverse = interleave(images["02"], images["01"])
    banner = (0x0989, "ЭСТАФЕТА - III")
    if banner not in list(strings(good)) or banner in list(strings(reverse)):
        raise ValueError("expected banner/interleaving evidence changed")
    for title, data in (("01 even / 02 odd", good), ("02 even / 01 odd (control)", reverse)):
        print(f"\n{title}: {len(data)} bytes, SHA-256 {hashlib.sha256(data).hexdigest()}")
        for offset, text in strings(data):
            print(f"{offset:04X}  {text!r}")


if __name__ == "__main__":
    main()
