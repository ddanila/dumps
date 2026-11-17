# MB007 — integrated video BIOS, Low / High pair

Source: MB007, a 286 mainboard with integrated video, per owner. Full physical
video chipset and EPROM markings remain unrecorded. This is separate from the
[system BIOS pair](../mb007-286-bios/).

## Acquisition — 2026-11-17

Both video BIOS chips are **27128**, Low and High per owner. Each produced
two identical 16,384-byte read-only T48 captures using `M27128A@DIP28`, with
chip-ID probing skipped. No programming or byte repairs were performed.

| Image | Size | CRC32 | Byte sum modulo 256 |
| --- | --- | --- | --- |
| [Low](mb007-video-bios-low.bin) | 16 KiB | `1870d66f` | `2E` |
| [High](mb007-video-bios-high.bin) | 16 KiB | `e55fb2a6` | `D2` |
| [Combined](mb007-video-bios-combined.bin) | 32 KiB | `c5e1265b` | `00` |

Low is interleaved into even byte addresses and High into odd addresses.
The resulting image starts `55 AA 40`: valid option-ROM signature and a declared
length of 64 × 512 = 32,768 bytes. The checksum across that length is zero.
No emulator or physical-board boot test has been performed.

## Firmware identification

- `IBM VGA Compatible BIOS.`
- `Chips 451 VGA BIOS.` at offset 0078h.
- `Version 2.0.1` at offset 008Dh.
- `Copyright (C) 1988 Chips and Technologies, Inc.  All Rights Reserved.`

This identifies the firmware family; physical video-chip markings remain unconfirmed.

SHA-256:

- Low: `d34ca970f6778a13c64129ca745e096f485ea59f9e52ef1b250971c4cbf86164`
- High: `9a5ac232dc5009884dbac71f752f74bf38248eada45710bf630c2bb29f9ba5e7`
- Combined: `99f982f8d3f2ffecb41d2fb70dc4b81f93b504045e15f3bf6a7b452229f1507f`

No match was found among 1,235 eligible 16–256 KiB files in the local 86Box ROM
collection. The Low comparison also checked extracted even/odd byte lanes.
Web searches for the firmware banner/version and CRC32 found no relevant public
candidate. This limited comparison does not establish uniqueness.

[Low evidence](evidence/low/) · [High and combined evidence](evidence/high/) ·
[Manifest](manifest.json)

[Inventory record](https://github.com/ddanila/vintage-computer-inventory/tree/main/items/MB007-286-integrated-video)
