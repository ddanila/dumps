# MB007 — 286 system BIOS, Low / High pair

Source: MB007, a 286 mainboard with integrated video, per owner. Manufacturer,
model, PCB revision, serial number and full chip labels remain unrecorded.

## Acquisition — 2026-11-17

Both system BIOS chips are **27256**, labelled **Low** and **High** per owner.
Each produced two identical 32,768-byte T48 reads using `M27256@DIP28`, with
chip-ID probing skipped. No programming or byte repairs were performed.

| Image | Size | CRC32 |
| --- | --- | --- |
| [Low](mb007-system-bios-low.bin) | 32 KiB | `fdf30486` |
| [High](mb007-system-bios-high.bin) | 32 KiB | `6b194b20` |
| [Combined](mb007-system-bios-combined.bin) | 64 KiB | `525d9105` |

Interleaving Low into even byte addresses and High into odd byte addresses
produces coherent text and an x86 reset jump `EA 5B E0 00 F0` at offset FFF0h
(to F000:E05B). Both chips and the combined image have byte sums modulo 256
of zero. These checks do not substitute for a boot test; none has been run.

## Firmware identification

- `80286 ROM BIOS PLUS Version 3.10`
- `Copyright (C) 1985-1989 Phoenix Technologies Ltd.`
- `CEC286  Subversion 02.04  06/12/1990`
- Reset-area date: `01/15/88` (distinct from the subversion banner date).

The `CEC286` identifier is recorded verbatim; it does not yet establish the
physical board manufacturer or model.

SHA-256:

- Low: `640d2dafe5c861ab34848a75a1163d6cdc5f25ce97f996efda85e5b5e3b52f95`
- High: `4cd243ca1a30366d7c1c5be726cd3fe6c10e83c162b3174f4085c6cb877dbf0a`
- Combined: `502cf1a0511549ad4c09288e7f96038cc0502840ee6d616f40d244d6ae6f0e03`

No match was found in 1,113 eligible 32–256 KiB files in the local 86Box ROM
collection. The Low comparison also checked extracted even/odd byte lanes.
Web searches for `CEC286` and its subversion found no relevant public candidate.
This limited comparison does not establish uniqueness.

[Low evidence](evidence/low/) · [High and combined evidence](evidence/high/) ·
[Manifest](manifest.json)

[Inventory record](https://github.com/ddanila/vintage-computer-inventory/tree/main/items/MB007-286-integrated-video)
