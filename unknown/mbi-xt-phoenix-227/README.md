# MBI XT Board / Phoenix 2.27 BIOS — raw capture

Read on 2026-11-17 from an owner-identified 2764 XT motherboard BIOS.
The originating motherboard and full chip markings are unknown. Attribution
comes from embedded `MBI XT Board`, Phoenix Technologies 1984–1986 copyright,
version 2.27, and date `05/29/86`. The reset vector is a far jump to F000:E05B.

## Acquisition

Three independent 8,192-byte T48 reads using `M2764A@DIP28` and `-x`
(skip electronic ID) match exactly. No programming was performed.
The canonical file is the unmodified first read. Logs, commands, tool hash,
string inventory and public comparison are in `evidence/`; the original three
binaries remain in the local session recorded in `manifest.json`.

SHA-256: `3f2b7bce83b44a0c5fe49a115a9c7cd174c6721c9c7c9c0371dc77ea17b107eb`

## Suspect byte; firmware integrity not confirmed

The full-image byte sum modulo 256 is **0xBE**, not zero. At offset **0x1F3A**,
the expected `B` of `ROM BIOS Ver 2.27` is **0x00**, producing `ROM \0IOS`.
Substituting 0x42 at that location would make the sum zero, but **no repair has
been applied**. Three matching reads establish repeatability, not the cause of
the anomaly or that the firmware is intact. A reseat/independent programmer
check would help distinguish a reading issue from stored contents.

## Public comparison

Compared against the [Minus Zero Degrees XT BIOS collection](https://www.minuszerodegrees.net/xt_clone_bios/xt_clone_bios.htm),
using its [Stuttgart mirror archive](https://computermuseum.informatik.uni-stuttgart.de/ftp/mirrors/www.minuszerodegrees.net/xt_clone_bios/Phoenix%20XT%20clone%20BIOS%20V2.27%20dated%2029MAY86.zip).
The reference is an 8 KiB Phoenix 2.27 image dated 29MAY86 with `YANGTECH.INC`
in place of `MBI XT Board`. It has a zero checksum. There are 14 differing bytes:

- Offset 0x0013: capture AE, reference FF, consistent with checksum adjustment
  for the changed board-name string.
- Offsets 0x06B8–0x06C3: board-name text.
- Offset 0x1F3A: capture 00, reference 42 (`B`).

All other bytes match. This supports an MBI-customized variant with one suspect
byte; it does not prove the physical chip's original contents. No exact public
match was found in this limited comparison. Preserve as a raw acquisition with
unresolved firmware integrity, not a verified working BIOS.
