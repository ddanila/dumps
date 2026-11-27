# NM27C512Q — pending analysis

Unidentified contents from a NM27C512Q EPROM. **Queued for future
analysis at the owner’s request (2026-11-27).** The originating device and
firmware identity are unknown.

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

## Deferred work

On a future explicit request, identify the contents, compare public firmware
collections, analyze the code/data, and decide whether to preserve the binary
in this repository. This record does not schedule or start that work.
