# Intel D27010 — pending analysis

Unidentified contents from an Intel D27010 EPROM. **Queued for further analysis;
analysis is deferred at the owner’s request (2026-11-27).** The originating
device and firmware identity are unknown.

## Acquisition

Read on 2026-11-27 using the T48 and `27C010@DIP32` profile with electronic
ID checking skipped (`-x`). Contacts passed; two successful 131,072-byte
reads matched. The capture is not blank: 87,098 bytes differ from FFh.
No programming or erasing was performed.

Both binaries, raw logs and the blank-check result remain in local session
`rom-programmers/sessions/intel-d27010-blank-check-20261127-065441`:
`read1.bin`, `read2.bin`, `read1.log`, `read2.log`, `result.json`.

SHA-256 (both reads):
`f8bf2df93c70c01c9f7b4bae5ce335a935d03deb4ba41bec691152e7bc041980`.

## Deferred work

On a future explicit request, identify the contents, compare public firmware
collections, analyze the code/data, and decide whether to preserve the binary
in this repository. This record does not schedule or start that work.
