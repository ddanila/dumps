# Edimax ISA-16 Ethernet remote boot V3.2

Owner-supplied orphan 2764, acquired 2026-11-14. Two 8192-byte captures match
exactly. Exact physical markings, manufacturer/suffix and originating board
are unknown; attribution comes from embedded text.

- CRC32: `7aae0416`
- SHA-1: `83b793818d2eccf572591fb4be20ca59a70ce8b4`
- SHA-256: `d68091931f2f13a97009f24b78dc1e27acfff2e3591a0d99e5d29eef9d1e7422`
- Header `55 AA 10`, declaring 8192 bytes; byte sum modulo 256 is **00**.
- No exact repeats at 128/256/512/1024/2048/4096-byte periods.

## Identification

Important text at decimal offsets:

| Offset | Text |
|---|---|
| 64 | Boot from Network (Y or N) ? |
| 317 | Novell Netware Remote BootROM V2.10 |
| 358 | (C) Copyright 1990 by |
| 381 | DIMAX/TOP HARVEST INT'L CORP. |
| 635 | NET$DOS.SYS / IBM$DOS.SYS / BOOTCONF.SYS |
| 3784 | Edimax ISA-16 Ethernet remote boot program V3.2 (931201) |
| 3871 | IRQ = 3 , I/O Base = 300h, no DMA or RAM |

The image is a PC network bootstrap loader with an Edimax adapter driver.
`931201` appears to mean 1993-12-01; it is not a proven manufacture date.
The 1990 copyright belongs to another embedded component/attribution and does
not conflict with a later driver date. The parameter text describes IRQ 3
and I/O base 300h, not independently measured card settings.

Other strings describe finding a server, opening/reading a boot disk image,
reading its configuration, DMA failure, Ethernet ROM/memory/hardware failure,
I/O and IRQ response failures, collisions, receive-buffer and packet errors.
The complete printable-run inventory is in `evidence/analysis.json`.
Network boot operation has not been tested; identification is based on the
ROM header, checksum and embedded strings.

## Acquisition

T48 firmware 00.1.03, minipro 0.7.4, `M2764A@DIP28`:

```sh
minipro -p M2764A@DIP28 -x -r OUTPUT.bin
```

Both commands exited zero; ID checks disabled. No programming or erase.
The profile reports 5 V read/verify VCC, not an independently measured rail.
Minipro warns about incomplete T48 support and outdated firmware. Logs remain
unchanged in `evidence/`. Full local session:
`dosravi/sessions/orphan-2764-t48-20261114-222508/`.

## Public-image comparison

On 2026-11-14, CRC32, SHA-1 and Edimax V3.2 remote-boot searches found no exact
public match. This is a bounded search, not proof of uniqueness.

- [E1160C NetWare V2.10 image](https://github.com/dlitz/E1160C-Netware-BootROM):
  same 8192-byte size but **3921 bytes differ**. The common V2.10 loader name
  does not identify the same binary.
- [86Box NE2000 image](https://github.com/86Box/roms/blob/master/network/ne2000/ne2000.rom):
  does not contain this capture at any offset.
- No exact match among the repository's existing 8192-byte images.

Comparator copies remain in the earlier local D-Link acquisition session;
comparison results are preserved in `evidence/comparisons.json`.

## Second matching acquisition

Another owner-supplied 2764 was read twice on 2026-11-15 in session
`orphan-2764-t48-20261115-144157`. Both 8192-byte captures match the
canonical image exactly, CRC32 `7aae0416`, option-ROM checksum 00.
Evidence is in `evidence/second-chip-20261115/`; no duplicate ROM is stored.
