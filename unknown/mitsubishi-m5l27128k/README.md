# Mitsubishi M5L27128K — Paradise VGA BIOS half

Likely odd-byte half of a Paradise VGA BIOS. Alternating characters preserve the Paradise copyright and IBM-compatible banner; the companion ROM and exact card/revision are unknown.

## Acquisition

Read on 2026-11-27 using the T48 and `27128@DIP28` profile with electronic
ID checking skipped (`-x`). Contacts passed; two successful 16,384-byte
reads matched. The capture is not blank: 16,135 bytes differ from FFh.
No programming or erasing was performed.

Both binaries, raw logs and the blank-check result remain in local session
`rom-programmers/sessions/m5l27128k-blank-check-20261127-070426`:
`read1.bin`, `read2.bin`, `read1.log`, `read2.log`, `result.json`.

SHA-256 (both reads):
`3a8fd648aa8312d516de6152fdac32d0f850e71bb7234b238a2fbf9c6bb2b1e5`.

## Public comparison — 2026-11-27

**Keep: no exact public match verified.** This does not establish that the dump is unique.

Compared against 1,834 files in [86Box/roms](https://github.com/86Box/roms/tree/de5a7d21982622def2c51a8e04119eea4119fc31), checking whole files and, for files twice the capture size, even/odd lanes and first/second halves. No match. The PCjs WDVGA PLUS 16 image and both DOS Days Philips PVGA1A-JK ROMs differ from this capture.

See [comparison.json](comparison.json) for source URLs, hashes and results. Both local reads remain intact. Full reverse engineering remains deferred.
