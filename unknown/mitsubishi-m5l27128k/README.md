# Mitsubishi M5L27128K — pending analysis

Unidentified contents from a Mitsubishi M5L27128K EPROM. **Queued for future
analysis at the owner’s request (2026-11-27).** The originating device and
firmware identity are unknown.

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

## Deferred work

On a future explicit request, identify the contents, compare public firmware
collections, analyze the code/data, and decide whether to preserve the binary
in this repository. This record does not schedule or start that work.
