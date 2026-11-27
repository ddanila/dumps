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

Compared against 1,834 files in [86Box/roms](https://github.com/86Box/roms/tree/de5a7d21982622def2c51a8e04119eea4119fc31), checking whole files and, for files twice the capture size, even/odd lanes and first/second halves. No match. MAME’s PC AT source does not list this capture’s SHA-1. A Sannata post offers an ALI1419 BIOS dated 12/12/91, but downloading it returned a site-verification HTML page, so it was not compared. The Retro Web also returned HTTP 403.

See [comparison.json](comparison.json) for source URLs, hashes and results. Both local reads remain intact. Full reverse engineering remains deferred.
