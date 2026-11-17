# GW-VGA Chips 451 BIOS v2.1.0

Recovered on 2026-11-17 from an owner-reported CHIPS VGA card BIOS EPROM,
28-pin DIP, exact markings unknown. Embedded identification:

- `GW-VGA 8 bits (Chips 451 VGA BIOS)`
- `Version 2.1.0`
- `Copyright (C) 1988, 1990 Chips and Technologies, Inc.`

The image also contains `For Evaluation Use Only.` Exact board manufacturer
and physical EPROM part number remain unconfirmed.

## Acquisition and validation

Two independent T48 reads using `M27256@DIP28`, with electronic ID probing
skipped (`-x`), match byte for byte. The 32,768-byte image begins `55 AA 40`:
its declared option-ROM length is 32 KiB and its byte sum modulo 256 is zero.
A further `M27C512@DIP28` read returns two identical copies of this image.
This is consistent with a 27256/27C256, but cannot distinguish address mirroring
from a larger chip deliberately containing duplicate halves. No programming
operation was performed. Supply reported 4.99 V; the reader emitted its existing
T48 support and firmware-version warnings. Raw logs are in `evidence/`.

SHA-256: `c57580813702064d5757fa9b1a5185dadd156f83d77e9e677d4ea847fdead415`

The original two reads and 64 KiB probe remain in the local acquisition session
recorded in `manifest.json`; the canonical binary is an unmodified 32 KiB read.

## Public comparison

On 2026-11-17, compared against the 86Box ROM collection's
[`ct82c450.bin`, `evga16.vbi`, and `wvga16s.bin`](https://github.com/86Box/roms/tree/master/video/chips).
No exact match found. Candidate hashes and sizes are recorded in
`evidence/analysis.json`. This limited search does not establish uniqueness.
[VGA Museum's F82C451 page](https://www.vgamuseum.info/index.php/news/item/178-chips-technologies-f82c451)
includes GW-VGA cards and a BIOS download, but the download returned HTTP 401
and could not be compared.
