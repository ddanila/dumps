# Perkin-Elmer TAC7/DX U35

Owner reports board TAC7/DX N519-9407 ISSUE T. U35 sticker reads
`N5208003 / U35 1999 / PERKIN-ELMER`. U36 (N5208004) is pending.

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
