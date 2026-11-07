# Norma Systems VMD-4: 27C512

Owner identifies a video-device board marked VMD-4 Mainboard, version 1.1,
Norma Systems, 1999. Physical chip label/socket reference was not supplied.
Separate acquisition from the earlier Beckman board.

One 65536-byte capture on 2026-11-07. CRC32 `bb16c7cb`; SHA256 in SHA256SUMS.
**Single read only: repeatability and bit-perfect chip contents remain unchecked.**
The DOS program exited zero and logged VCC off/VPP off. Transport downloaded
and CRC-checked the file. Read time including chunk I/O: 357940 ms (5m58s).
Serial upload needed retries and took much longer than normal; those delays
are separate from the recorded read time.

At offset 0090 the image says:

> SOFTWARE VMD-4  VERSION >>1.01<< DATUM 04/10/99 - designed by M.Skau 1999 - without Millenium-Bug

The date is preserved literally without assuming day/month order. There are
3925 nonzero bytes; the last is at 1570h. All bytes 1571h–FFFFh are zero.
Halves differ and the whole image is not a short repeating pattern. Initial
02 01 0A and interrupt-vector patterns suggest 8051-family code; CPU identity
has not been confirmed from the board. Keep the entire capture, including padding.

Read with RD512F1.COM, build dosravi-27512-fastaddr-v1, command R27512 with
/PROFILE:conservative /FASTADDR, on Pocket8086 LPT378h and Willem PCB5.0E.
Normal J1/J2, DIP1D4 (ON 3,5,7,8,9), J9/J10 toward DB25, 5V VCC,
programming VPP off, 28-pin chip bottom-aligned with two empty rows by lever.
Owner confirmed readiness after settings were supplied; no new rail measurement
was reported. CP2102 /dev/ttyUSB1 at 57600 baud.

Evidence preserves original bytes. WILLEM.LOG is cumulative; identify this run
by C512R1.BIN and build ID. DOS time is 1980; acquisition uses host date.
The provenance addendum supersedes the initially unspecified board in session.json.
Full serial logs remain in the local source session recorded in manifest.json.

Targeted web searches on acquisition date for Norma Systems VMD-4, the exact
firmware banner/author and CRC32 found no matching dump. No candidate binary
was available to compare; this is not an exhaustive search or proof of uniqueness.

[Static firmware analysis: parallel flash and persistent settings](../analysis/README.md).
