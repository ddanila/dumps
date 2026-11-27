# NM27C512Q — AMI FA3 ISA system BIOS

AMI FA3 ISA motherboard BIOS, dated `12/12/91`, with ID `40-01AE-001247-00101111-121291-ALI1419`. The exact motherboard is unconfirmed.

## Acquisition

Read on 2026-11-27 using the T48 and `NM27C512@DIP28` profile with electronic
ID checking skipped (`-x`). Contacts passed; two successful 65,536-byte
reads matched. The capture is not blank: 64,825 bytes differ from FFh.
No programming or erasing was performed.

Both binaries, raw logs and the blank-check result remain in local session
`rom-programmers/sessions/nm27c512q-blank-check-20261127-070629`:
`read1.bin`, `read2.bin`, `read1.log`, `read2.log`, `contacts.log`, `result.json`.

SHA-256 (both reads):
`ffa9fecaa866a7f5e0efc35aa7cd0c435bc651baa2c7c168d47564c039012e7b`.

## Public comparison — 2026-11-27

**Keep: no exact public match verified.** This does not establish that the dump is unique.

Compared against 1,834 files in [86Box/roms](https://github.com/86Box/roms/tree/de5a7d21982622def2c51a8e04119eea4119fc31), checking whole files and, for files twice the capture size, even/odd lanes and first/second halves. No match. MAME’s PC AT source does not list this capture’s SHA-1. The owner subsequently supplied four archives downloaded from Sannata and The Retro Web; all four contain 65,536-byte images.

| Candidate | Bytes differing from capture |
| --- | ---: |
| `abit-386dx-fa3.zip` / `ABITFA3.BIN` | 4 |
| `AMI_386_ALI1419_121291.7z` / `AMI_386_ALI1419_121291.BIN` | 48 |
| `za633995.zip` / `ZA633995.bin` | 33,714 |
| `pt-3401.zip` / `PT-3401.bin` | 31,496 |

The closest image comes from [The Retro Web’s Abit AB-FA3 page](https://theretroweb.com/motherboards/s/abit-ab-fa3). It matches 65,532 of 65,536 bytes, strongly associating this firmware with that family. At offsets `E13E`, `E13F`, `E145`, and `E14B`, the capture contains `00`, whereas the public image contains `04`, `0C`, `08`, and `11`. The cause of these differences is not established; do not treat either copy as a verified correction of the other. Both local reads agree, and neither public candidate is an exact duplicate.

See [comparison.json](comparison.json) for source URLs, hashes and results. Both local reads remain intact. Full reverse engineering remains deferred.

### Four-byte difference context

| File offset | Local capture (both reads) | Public ABITFA3.BIN | Sannata image |
| --- | --- | --- | --- |
| `0xE13E` | `00` | `04` | `00` |
| `0xE13F` | `00` | `0C` | `00` |
| `0xE145` | `00` | `08` | `00` |
| `0xE14B` | `00` | `11` | `00` |

All four are in the zero-filled region `0xE139–0xE15F`, immediately after
AMI’s copyright/address/telephone text and before a repeated data structure
starting at `0xE160`. They are not changes to that text. The independently
sourced Sannata image agrees with the local zero bytes at these positions,
although it differs elsewhere (including BIOS identification, banner and code).
This supports retaining the local image as a distinct capture; it does not
establish whether the public nonzero bytes are intentional data or corruption.
No bytes have been patched or discarded.
