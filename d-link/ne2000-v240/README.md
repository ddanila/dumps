# D-Link NE2000 BootROM Driver V2.40 / Novell NetWare loader

An 8 KiB PC option ROM with 16-bit x86 network-bootstrap code: D-Link's
NE2000 boot driver and a Novell NetWare remote DOS loader. It comes from an
orphan chip (a 2764, per the owner); the board, manufacturer and sticker text
are unknown. The D-Link attribution comes from the firmware, not from the chip.

## Acquisition

Read on 2026-11-14. Two independent 8192-byte reads match exactly.

- SHA-256: `0de28d3a3c23fcba5fa679305ccad17604fd281c37fc4507425210cf562a2997`
- SHA-1: `7095143756fb3c13b3205063ea12a8ccc9ec1491`
- CRC32: `d03c2ee5`
- Header: `55 AA 10`; declares 16 × 512 = 8192 bytes.
- Byte sum modulo 256: **00**, a valid PC option-ROM checksum.
- No identical 128/256/512/1024/2048/4096-byte repeating period.

Matching reads and an independently valid checksum give confidence in the
capture. They are not a full electrical test and do not confirm the exact chip
type.

## Acquisition

T48 firmware 00.1.03, minipro 0.7.4, profile `M2764A@DIP28`:

```sh
minipro -p M2764A@DIP28 -x -r OUTPUT.bin
```

Both commands returned zero; 8192 bytes each, zero differing bytes. ID checks
were disabled. No programming, erase, ID voltage probing or firmware upgrade.
The selected profile reports 5 V verify/read VCC; programming-voltage defaults
were not used. No independent chip-pin voltage measurement was made.
Minipro warns about incomplete T48 support and outdated firmware. Original
read logs and metadata are in `evidence/`. Full local session:
`dosravi/sessions/orphan-next-2764-t48-20261114-221613/`.

## Identification and behavior

Important embedded text (hex offsets):

| Offset | Text |
|---|---|
| 0040 | Boot from Network (Y or N) ? |
| 0144 | Novell NetWare Remote Program Loader |
| 016D | Copyright 1988 Novell, Inc. |
| 01A9 | Error initializing Network Interface Board. |
| 01D7 | Error finding server. |
| 01EF | Error opening boot disk image file |
| 0214 | Error reading boot disk image file. |
| 023A | Error reading configuration file. |
| 0282 | NET$DOS.SYS / IBM$DOS.SYS / BOOTCONF.SYS |
| 0D28 | D-Link NE2000 BootROM Driver V2.40 |
| 12D8 | BE-200 |
| 16E5 | Error loading remote boot sector. Please re-boot. |
| 19F3 | D-Link NE2000 BootROM Driver V2.40 |
| 1A1A | Memory failure |
| 1A37 | IRQ failure |
| 1A51 | I/O failure |
| 1E38 | Hardware setting(s) incorrect ! |

1988 is a copyright date, not a proven build date. `BE-200` is another embedded
identifier, insufficient to determine the original card. Configuration descriptions
include I/O bases 300h, 320h, 340h and 360h, not proof of actual card jumpers.
Full printable runs are in `evidence/analysis.json`, including incidental
machine-code matches. Some messages in the table omit decorative punctuation.

Disassembly of entry 0003 shows that it preserves AX/ES, checks the installation
marker at physical 00304, saves the current INT 19h vector at 00300, installs
CS:0061 as the new bootstrap handler, writes marker 6A6Eh and returns far.
A second call sees the marker and leaves the saved vector alone.

The handler at 0061 uses BIOS INT 13h to reset/read drive 0. A successful sector
read restores the old INT 19h vector and invokes it. After four failed attempts,
it queries hard disk 80h. If a disk is reported, it prompts whether to boot from
the network, reads Y/N through INT 16h and restores the previous bootstrap on N.
The network path obtains conventional-memory size with INT 12h, calculates a RAM
relocation address, copies the ROM and jumps into its relocated loader. Embedded
filenames and diagnostics identify its purpose as loading a DOS boot image from
a NetWare server. No server exchange or end-to-end network boot was emulated.

## Executed verification

`analysis/check_entry.py` runs the original installer twice in Unicorn 2.1.4 with
synthetic BIOS RAM and a far-return sentinel. Both calls return. First call
installs C800:0061, retains the original vector and writes the marker; second
call preserves that state. Results: `analysis/entry-results.json`. This tests
only the installer, not the NIC or network-loader implementation.

```sh
python3 -m venv /tmp/ne2000-check
/tmp/ne2000-check/bin/pip install unicorn==2.1.4
/tmp/ne2000-check/bin/python analysis/check_entry.py
sha256sum -c SHA256SUMS
```

## Public availability check

No exact public match found as of 2026-11-14. This is a bounded search, not a
claim that this image has never been published.

- CRC32, SHA-1 and complete driver/version-string searches found no identifiable
  exact download.
- [86Box NE2000 image](https://github.com/86Box/roms/blob/master/network/ne2000/ne2000.rom):
  downloaded, 64000 bytes, CRC32 F726AD64; does not contain this 8192-byte capture
  at any offset.
- [E1160C NetWare ROM](https://github.com/dlitz/E1160C-Netware-BootROM): downloaded,
  8192 bytes, CRC32 93083785; 7075 differing bytes. Its embedded version is V2.10,
  versus this image's D-Link driver V2.40. Similar messages do not imply the same
  image, or that these version numbers refer to the same software component.
- [ZXnet's collection](https://www.zx.net.nz/netware/client/rpl_rom.shtml) and
  [D-Link's directory](https://ftp.dlink.ru/pub/Bootrom/Firmware/) were inspected
  for candidates. DE224C entries have different version labels; their contents
  were not downloaded/compared. The linked minuszerodegrees DE-150 download
  returned HTTP 406 and remains untested.

Comparator files stay in the local session, outside this preservation directory.

## Second matching chip

A second owner-supplied 2764 was read twice on 2026-11-14 (session
`orphan-2764-t48-20261114-222425`). Both 8192-byte captures match each other
and the canonical image byte-for-byte, CRC32 `d03c2ee5`, checksum 00.
Logs and acquisition metadata are in `evidence/second-chip-20261114/`;
no duplicate ROM binary is stored. Full markings and originating board
remain unknown.

## Third matching acquisition

Another owner-supplied 2764 was read twice in session
`orphan-2764-t48-20261114-223304`. Both 8192-byte captures match the
canonical image exactly, CRC32 `d03c2ee5`, option-ROM checksum 00.
Evidence is in `evidence/third-chip-20261114/`; no duplicate ROM is stored.
This confirms successful nonblank reading after several intervening all-FF
chips; it does not establish whether those earlier chips were erased or faulty.

## Fourth matching acquisition

Another owner-supplied 2764 was read twice on 2026-11-15 in session
`orphan-2764-t48-20261115-144024`. Both 8192-byte captures match the
canonical image exactly, CRC32 `d03c2ee5`, option-ROM checksum 00.
Evidence is in `evidence/fourth-chip-20261115/`; no duplicate ROM is stored.

## Fifth matching acquisition

Another owner-supplied 2764 was read twice on 2026-11-16 in session
`orphan-2764-t48-20261116-105320`. Both 8192-byte captures match the
canonical image exactly, CRC32 `d03c2ee5`, option-ROM checksum 00.
Evidence is in `evidence/fifth-chip-20261116/`; no duplicate ROM is stored.

## Sixth matching acquisition

Another owner-supplied 2764 was read twice on 2026-11-16 in session
`orphan-2764-t48-20261116-185816`. Both 8192-byte captures match the
canonical image exactly, CRC32 `d03c2ee5`, option-ROM checksum 00.
Evidence is in `evidence/sixth-chip-20261116/`; no duplicate ROM is stored.

## Seventh matching acquisition

Another owner-supplied 2764 was read twice on 2026-11-16 in session
`orphan-2764-t48-20261116-191144`. Both 8192-byte captures match the
canonical image exactly, CRC32 `d03c2ee5`, option-ROM checksum 00.
Evidence is in `evidence/seventh-chip-20261116/`; no duplicate ROM is stored.

## Eighth matching acquisition

Another owner-supplied 2764 was read twice on 2026-11-16 in session
`orphan-2764-t48-20261116-192424`. Both 8192-byte captures match the
canonical image exactly, CRC32 `d03c2ee5`, option-ROM checksum 00.
Evidence is in `evidence/eighth-chip-20261116/`; no duplicate ROM is stored.

## Ninth matching acquisition

Another owner-supplied 2764 was read twice on 2026-11-16 in session
`orphan-2764-t48-20261116-192950`. Both 8192-byte captures match the
canonical image exactly, CRC32 `d03c2ee5`, option-ROM checksum 00.
Evidence is in `evidence/ninth-chip-20261116/`; no duplicate ROM is stored.

## Tenth matching acquisition

Another owner-supplied 2764 was read twice on 2026-11-17 in session
`orphan-2764-t48-20261117-204348`. Both 8192-byte captures match the
canonical image exactly, CRC32 `d03c2ee5`, option-ROM checksum 00.
Evidence is in `evidence/tenth-chip-20261117/`; no duplicate ROM is stored.

## Eleventh matching acquisition

Another owner-supplied 2764 was read twice on 2026-11-17 in session
`orphan-2764-t48-20261117-204452`. Both 8192-byte captures match the
canonical image exactly, CRC32 `d03c2ee5`, option-ROM checksum 00.
Evidence is in `evidence/eleventh-chip-20261117/`; no duplicate ROM is stored.
