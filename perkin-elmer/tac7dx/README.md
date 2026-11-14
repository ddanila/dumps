# Perkin-Elmer TAC7/DX U35 and U36

Owner reports board TAC7/DX N519-9407 ISSUE T. U35 sticker reads
`N5208003 / U35 1999 / PERKIN-ELMER`. U36 sticker reads `N5208004 / U36 1999 / PERKIN-ELMER`.

Read twice on 2026-11-14 with T48 firmware 00.1.03 and minipro 0.7.4:
`minipro -p M27256@DIP28 -x -r OUTPUT.bin`. Both operations exited 0.
ID probing was disabled. No program or erase command was issued.
Profile VCC is 5 V; this is not an independent chip-rail measurement.

The preserved raw 32768-byte capture has two identical 16384-byte halves,
with nonblank data and all 256 byte values. Both reads match byte for byte.
No trimming was performed. Repeatability does not prove chip type or complete
physical capacity. The schematic specifies 27128 for U35; under a 27256
profile pin 27 is A14, whereas on a 27128 it is /PGM. The upper half is the
candidate 16 KiB image. The 1999 stickers differ from older manual part numbers.

Source: [Perkin-Elmer technical information, sheet 1, PDF page 7](https://www.artisantg.com/info/Perkin_Elmer_TAC7dx_Technical_Information.pdf).

Minipro warns of incomplete T48 support and older-than-expected programmer
firmware. Original read logs are in evidence; reader hash and acquisition
metadata are in manifest.json. Searches for the sticker and controller ROMs
found no relevant downloadable candidate to compare; Internet uniqueness is
not established. Full sessions remain at the path recorded in the manifest.

## U36 acquisition

Read U36 twice on 2026-11-14 with the same T48 and M27256 profile, with
ID probing disabled. Both commands exited 0 and produced identical
32768-byte nonblank captures. Unlike U35, U36 has different lower and upper
16 KiB halves. All 256 byte values are present. The full raw image is
`u36-n5208004-27256-read.bin`; CRC32 is `d6d56190`.

The result is consistent with the schematic's 27256 capacity, but exact
physical device identity remains unconfirmed. Repeatability alone is not
functional validation of the firmware. U36 logs are in evidence and its
metadata is the second entry in manifest.json. Public searches found the
service manual and hardware listings, but no downloadable ROM candidate
to compare. Both chips are now captured; U35's raw duplicated half is retained.

## Firmware analysis and execution

The [analysis report and reproducible harness](analysis/README.md) establish
that these images contain a 6809 program identifying itself as
`TAC7,N5208003REVA`. Both embedded checksums pass. With synthetic peripherals,
the original ROMs pass startup diagnostics and reach the main service loop.
The analysis also exercises 64 parser requests, two startup failures and
the periodic acquisition interrupt. This is functional evidence beyond
repeat reads; the harness is not a complete physical-instrument emulator.
