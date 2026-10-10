# Robotron PC1715 S642 keyboard firmware

2 KiB firmware marked **S642**, read from an owner-identified Soviet РФ2
(2716 equivalent) EPROM. The owner identifies the keyboard as dual-language.
S642 is documented for PC1715 Latin/Cyrillic keyboard variants; the exact
keyboard subtype has not been independently established.

[Download the ROM](s642.ic8) · [Submission ZIP](s642-dump.zip) · [Manifest](manifest.json)

## Verification

Two independent reads on 2026-10-10 match byte-for-byte. Both completed with
VCC/VPP off. CRC32: `5c9ca8dc`; SHA-1:
`73800997e8fe6410d63573330126d4e12feb7267`.
SHA-256 is recorded in [SHA256SUMS](SHA256SUMS).

MAME 0.285 executed the unchanged ROM in its existing keyboard model:

- All 91 mapped non-modifier positions returned framed status/keycode pairs.
- Shift, Control, Caps, SI/SO and release/repress checks passed.
- Across 182 key/Shift combinations, SI/SO toggled status bit `04`, retained
  the keycode byte, and a second toggle restored the original output.
- Published S600 passed the same functional harness; a blank-ROM control failed.

These tests establish useful keyboard behavior, not full-system boot,
physical timing accuracy, or a bit-perfect match to an original reference.
Host/display interpretation of the language flag and physical key legends
remain unverified.

## Acquisition

Willem PCB5.0E, Pocket8086 LPT 378h, DOSRAVI over CP2102 at 57600 baud.
Commands: `S642RD.COM RRF5 S642R1.BIN 378 /PROFILE:conservative` and the
same command with `S642R2.BIN`. Read times: 28,050 and 28,105 ms.
The reader identity is recorded in the manifest.

The standard 2716 setup was specified: special J1/J2 routing, J9/J10 toward
DB25, DIP ON 1/2/6/8/9, 5 V VCC and programming VPP off. Physical routing
and voltages were not independently measured during this session.

[evidence/](evidence/) preserves unmodified stdout, session metadata,
execution identities and cumulative programmer logs. Earlier operations
appear in WILLEM.LOG; each final run is the relevant acquisition. DOS clock
values are not the acquisition date. Initial session notes call provenance
tentative; the owner subsequently confirmed the dual-language keyboard.
Full serial logs remain in the local DOSRAVI acquisition sessions.

## Public comparison

No downloadable S642 reference was found in the collections checked on
2026-10-10. [MAME](https://github.com/mamedev/mame/blob/master/src/mame/robotron/rt1715.cpp)
listed S642 as `NO_DUMP`; [OldPC](https://oldpc.su/articles/de_roms/DE_ROMs.html)
listed the part without a download. This is not a claim of global uniqueness.
The [Tiffe archive](https://www.tiffe.de/Robotron/PC1715/EPROM/ROMs-PC1715.zip)
contains S600 and S618; this capture differs from each at 188 of 2,048 bytes.

MAME's historical `CCITT 962e` comment is unresolved: the capture gives
`46ab` with CRC-CCITT initial value `ffff`, and `832f` with initial value zero.
The manual lists S642 values `962e` and `da68` for different country variants.
No equivalence to either documented value is asserted.

## Reproduce the emulator tests

From `emulation/`, run `python3 run.py` then `python3 analyze.py`.
Repeat from `emulation/language-test/` for the continuous language sweep.
Requires `/usr/games/mame` with the rt1715 driver and Python 3.
Saved traces are gzip-compressed; running the scripts regenerates them.

The harness supplies a HALT host ROM and placeholder host data, and loads
S642 in the existing S600 keyboard slot. ROM audit warnings are expected.
The general tests restart firmware initialization between cases; the language
sweep deliberately runs continuously without resets.
Positive and negative control results are in `emulation/s600/` and
`emulation/blank/`; reference firmware is not duplicated here.
