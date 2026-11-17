# EFA IES16-series Novell RPL boot ROM

Read on 2026-11-14 from an orphan chip reported by the owner as a 2764.
Two independent 8192-byte reads match exactly. Exact chip manufacturer/suffix,
label and originating card are unknown. Identification below is from ROM text.

- SHA-256: `8948a241119cc8fe3fa5849d5dfffc024aaaad21d1cef53b748a978f285f3beb`
- SHA-1: `17bcb6a56bf7f5742a6a1ed1c48e50550c60fa64`
- CRC32: `95abede4`
- PC option-ROM header `55 AA 10`: 8192 bytes declared.
- Byte sum modulo 256: **00**, valid option-ROM checksum.
- No exact repetition at 128, 256, 512, 1024, 2048 or 4096 bytes.

## Identification

| Decimal file offset | Embedded text |
|---|---|
| 1221 | VeRsIoN=Novell RPL BootROM v1.00 (920626) |
| 1329 | Boot From Netware Server |
| 3845 | IES16 series (NE2000 Compatible) |
| 6064 | VeRsIoN=EFA IES16 series MLID v1.0B (940331) |
| 6110 | (C) Copyright 1994 EFA Corporation of America. |
| 6182 | LINK DRIVER IES16 |

Whitespace and decorative characters are simplified in the table; exact printable
runs are in `evidence/analysis.json`. Dates appear to mean 1992-06-26 for the RPL
component and 1994-03-31 for the adapter driver, not independently verified
manufacture dates. Messages include transmit timeout, incomplete DMA, NIC
reinitialization, receive-buffer error, command-port failure, RAM-buffer failure
and inability to find an adapter.

This is 16-bit PC x86 firmware for network startup, with a Novell RPL loader and
an EFA IES16 adapter driver. Unlike the previous D-Link V2.40 acquisition, this
image explicitly identifies itself as RPL.

Static disassembly of entry 0003h shows it saves the existing INT 19h vector at
physical 00300h, installs CS:003Ah as the boot handler, and writes marker 0622h
at physical 00304h before a far return. A matching marker skips reinstallation.
No end-to-end network boot or hardware test was performed.

## Acquisition

T48 firmware 00.1.03, minipro 0.7.4:

```sh
minipro -p M2764A@DIP28 -x -r OUTPUT.bin
```

Both commands exited zero. ID test disabled; no programming or erasing.
Profile uses 5 V verify/read VCC; this is not an independent chip-pin measurement.
Minipro warns that T48 support is incomplete and its firmware is outdated.
Original logs are preserved unchanged in `evidence/`.
Full captures and session metadata remain at
`/home/ddanila/fun/dosravi/sessions/orphan-bootrom-2764-t48-20261114-222124/`.

## Availability check

No exact public match found on 2026-11-14. CRC32, SHA-1, EFA IES16 and BootROM
string searches did not locate an exact downloadable image. This is not proof
of uniqueness. The generic Novell RPL version string is shared by other ROMs
and does not establish an exact match.

Compared against the already-downloaded
[86Box NE2000 ROM](https://github.com/86Box/roms/blob/master/network/ne2000/ne2000.rom)
and [E1160C NetWare ROM](https://github.com/dlitz/E1160C-Netware-BootROM): neither
contains this 8192-byte image at any offset. Searches of the local MAME source
found no matching CRC32, SHA-1 or IES16 identifier. Other public archives have
not been exhaustively checked.

## Second matching acquisition

Another owner-supplied 2764 was read twice on 2026-11-15 in session
`orphan-2764-t48-20261115-144302`. Both 8192-byte captures match the
canonical image exactly, CRC32 `95abede4`, option-ROM checksum 00.
Evidence is in `evidence/second-chip-20261115/`; no duplicate ROM is stored.

## Third matching acquisition

Another owner-supplied 2764 was read twice on 2026-11-15 in session
`orphan-2764-t48-20261115-165239`. Both 8192-byte captures match the
canonical image exactly, CRC32 `95abede4`, option-ROM checksum 00.
Evidence is in `evidence/third-chip-20261115/`; no duplicate ROM is stored.

## Fourth matching acquisition

Another owner-supplied 2764 was read twice on 2026-11-16 in session
`orphan-2764-t48-20261116-104905`. Both 8192-byte captures match the
canonical image exactly, CRC32 `95abede4`, option-ROM checksum 00.
Evidence is in `evidence/fourth-chip-20261116/`; no duplicate ROM is stored.

## Fifth matching acquisition

Another owner-supplied 2764 was read twice on 2026-11-16 in session
`orphan-2764-t48-20261116-105624`. Both 8192-byte captures match the
canonical image exactly, CRC32 `95abede4`, option-ROM checksum 00.
Evidence is in `evidence/fifth-chip-20261116/`; no duplicate ROM is stored.

## Sixth matching acquisition

Another owner-supplied 2764 was read twice on 2026-11-16 in session
`orphan-2764-t48-20261116-110237`. Both 8192-byte captures match the
canonical image exactly, CRC32 `95abede4`, option-ROM checksum 00.
Evidence is in `evidence/sixth-chip-20261116/`; no duplicate ROM is stored.

## Seventh matching acquisition

Another owner-supplied 2764 was read twice on 2026-11-16 in session
`orphan-2764-t48-20261116-185557`. Both 8192-byte captures match the
canonical image exactly, CRC32 `95abede4`, option-ROM checksum 00.
Evidence is in `evidence/seventh-chip-20261116/`; no duplicate ROM is stored.

## Eighth matching acquisition

Another owner-supplied 2764 was read twice on 2026-11-16 in session
`orphan-2764-t48-20261116-185930`. Both 8192-byte captures match the
canonical image exactly, CRC32 `95abede4`, option-ROM checksum 00.
Evidence is in `evidence/eighth-chip-20261116/`; no duplicate ROM is stored.

## Ninth matching acquisition

Another owner-supplied 2764 was read twice on 2026-11-16 in session
`orphan-2764-t48-20261116-190810`. Both 8192-byte captures match the
canonical image exactly, CRC32 `95abede4`, option-ROM checksum 00.
Evidence is in `evidence/ninth-chip-20261116/`; no duplicate ROM is stored.

## Tenth matching acquisition

Another owner-supplied 2764 was read twice on 2026-11-16 in session
`orphan-2764-t48-20261116-190944`. Both 8192-byte captures match the
canonical image exactly, CRC32 `95abede4`, option-ROM checksum 00.
Evidence is in `evidence/tenth-chip-20261116/`; no duplicate ROM is stored.

## Eleventh matching acquisition

Another owner-supplied 2764 was read twice on 2026-11-16 in session
`orphan-2764-t48-20261116-191605`. Both 8192-byte captures match the
canonical image exactly, CRC32 `95abede4`, option-ROM checksum 00.
Evidence is in `evidence/eleventh-chip-20261116/`; no duplicate ROM is stored.

## Twelfth matching acquisition

Another owner-supplied 2764 was read twice on 2026-11-16 in session
`orphan-2764-t48-20261116-191703`. Both 8192-byte captures match the
canonical image exactly, CRC32 `95abede4`, option-ROM checksum 00.
Evidence is in `evidence/twelfth-chip-20261116/`; no duplicate ROM is stored.

## Thirteenth matching acquisition

Another owner-supplied 2764 was read twice on 2026-11-16 in session
`orphan-2764-t48-20261116-191755`. Both 8192-byte captures match the
canonical image exactly, CRC32 `95abede4`, option-ROM checksum 00.
Evidence is in `evidence/thirteenth-chip-20261116/`; no duplicate ROM is stored.

## Fourteenth matching acquisition

Another owner-supplied 2764 was read twice on 2026-11-16 in session
`orphan-2764-t48-20261116-191915`. Both 8192-byte captures match the
canonical image exactly, CRC32 `95abede4`, option-ROM checksum 00.
Evidence is in `evidence/fourteenth-chip-20261116/`; no duplicate ROM is stored.

## Fifteenth matching acquisition

Another owner-supplied 2764 was read twice on 2026-11-16 in session
`orphan-2764-t48-20261116-192025`. Both 8192-byte captures match the
canonical image exactly, CRC32 `95abede4`, option-ROM checksum 00.
Evidence is in `evidence/fifteenth-chip-20261116/`; no duplicate ROM is stored.

## Sixteenth matching acquisition

Another owner-supplied 2764 was read twice on 2026-11-16 in session
`orphan-2764-t48-20261116-192314`. Both 8192-byte captures match the
canonical image exactly, CRC32 `95abede4`, option-ROM checksum 00.
Evidence is in `evidence/sixteenth-chip-20261116/`; no duplicate ROM is stored.

## Seventeenth matching acquisition

Another owner-supplied 2764 was read twice on 2026-11-16 in session
`orphan-2764-t48-20261116-193049`. Both 8192-byte captures match the
canonical image exactly, CRC32 `95abede4`, option-ROM checksum 00.
Evidence is in `evidence/seventeenth-chip-20261116/`; no duplicate ROM is stored.

## Eighteenth matching acquisition

Another owner-supplied 2764 was read twice on 2026-11-16 in session
`orphan-2764-t48-20261116-200422`. Both 8192-byte captures match the
canonical image exactly, CRC32 `95abede4`, option-ROM checksum 00.
Evidence is in `evidence/eighteenth-chip-20261116/`; no duplicate ROM is stored.

## Nineteenth matching acquisition

Another owner-supplied 2764 was read twice on 2026-11-16 in session
`orphan-2764-t48-20261116-200518`. Both 8192-byte captures match the
canonical image exactly, CRC32 `95abede4`, option-ROM checksum 00.
Evidence is in `evidence/nineteenth-chip-20261116/`; no duplicate ROM is stored.

## Twentieth matching acquisition

Another owner-supplied 2764 was read twice on 2026-11-17 in session
`orphan-2764-t48-20261117-101217`. Both 8192-byte captures match the
canonical image exactly, CRC32 `95abede4`, option-ROM checksum 00.
Evidence is in `evidence/twentieth-chip-20261117/`; no duplicate ROM is stored.

## Twenty-first matching acquisition

Another owner-supplied 2764 was read twice on 2026-11-17 in session
`orphan-2764-t48-20261117-204034`. Both 8192-byte captures match the
canonical image exactly, CRC32 `95abede4`, option-ROM checksum 00.
Evidence is in `evidence/twenty-first-chip-20261117/`; no duplicate ROM is stored.

## Twenty-second matching acquisition

Another owner-supplied 2764 was read twice on 2026-11-17 in session
`orphan-2764-t48-20261117-204211`. Both 8192-byte captures match the
canonical image exactly, CRC32 `95abede4`, option-ROM checksum 00.
Evidence is in `evidence/twenty-second-chip-20261117/`; no duplicate ROM is stored.

## Twenty-third matching acquisition

Another owner-supplied 2764 was read twice on 2026-11-17 in session
`orphan-2764-t48-20261117-204621`. Both 8192-byte captures match the
canonical image exactly, CRC32 `95abede4`, option-ROM checksum 00.
Evidence is in `evidence/twenty-third-chip-20261117/`; no duplicate ROM is stored.
