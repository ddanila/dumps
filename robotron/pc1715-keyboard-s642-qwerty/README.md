# Robotron PC1715 S642 — QWERTY/ЯВЕРТЫ keyboard

2 KiB firmware from a second owner-identified РФ2 (2716-equivalent) EPROM
labelled **S642**. The owner reports QWERTY/ЯВЕРТЫ key legends, unlike the
[previous S642 keyboard](../pc1715-keyboard-s642/) with ЙЦУКЕН/JCUKEN legends.
The chips and labels look identical; the ROM images differ.

[ROM](s642-qwerty.bin) · [Submission ZIP](s642-qwerty-dump.zip) · [Manifest](manifest.json)

## Acquisition and comparison

Two independent reads on 2026-10-10 match byte-for-byte. Each read took
28,050 ms and exited successfully with VCC/VPP off. The image contains 219
distinct byte values and has no repeated 16/32/64/128/256/512/1024-byte period.

- CRC32: `1cdfa673`
- SHA-1: `40bfa73bab31ac7156750e38bdba5e6f2588752f`
- SHA-256: `a5e07d8c7b5738c79af8e23847a5d0e7a5bbcde6a73e2826689e3d38c8c02748`

Compared with the earlier S642, 154 bytes differ, all in the two 256-byte
keycode tables at `0460–055F` and `0560–065F`. The rest of the image,
including the firmware code, is identical. The table lookup selects mirrored
ROM addresses `4460`/`4560`. [Byte differences](comparison.tsv) are preserved.
The emulated letter positions emit `qwerty`, confirming the reported variant.

The old MAME comment `CCITT 962e` does **not** match this capture under either
checked CRC-CCITT initialization: `ffff` gives `7d59`; zero gives `b8dd`.
Its historical checksum convention remains unresolved.

This image also differs from the [Tiffe archive](https://www.tiffe.de/Robotron/PC1715/EPROM/ROMs-PC1715.zip)
S600 and S618 images at 85 and 92 bytes respectively. Searches for this
CRC32/SHA-1 on 2026-10-10 found no matching public reference; this is not a
claim of global uniqueness.

## Validation

The unchanged image passed the existing isolated keyboard harness in MAME
0.285, plus explicit expected-code checks for the QWERTY alphabet:

- 205 general checks: 91 matrix positions, serial framing, Shift, Control,
  Caps, SI/SO, release/repress and stable held-key output.
- 548 continuous cases covering 182 position/Shift combinations through
  Latin → alternate language → Latin, without firmware resets.
- SI/SO toggles status bit `04`, keeps the keycode unchanged and restores the
  original pair on a second toggle. SI/SO alone sends no bytes. Language LED
  I/O is active only in the alternate mode.
- All 26 alphabet keys produce their expected ASCII codes in both Shift
  states: 52 explicit checks.

Full-system tests booted the **original TOS/M disk**, with its original
COMMON0/KOI71 font order, on `rt1715w` using MAME 0.289 with
[PR #6's font-selector implementation](https://github.com/ddanila/mame/pull/6).
Physical matrix injection of the top-row keys produced `qwerty`; SI/SO plus
another key displayed **ЯВЕРТЫ**, then the second toggle restored Latin.
Pixel comparisons verified changed glyphs and exact restoration of the static
heading. Stock MAME 0.285 received identical keyboard/OS traffic but did not
switch fonts. [Traces and screenshots](emulation/end-to-end/) are preserved.

These are automated tests of this second acquisition. The earlier owner's
manual end-to-end confirmation applies to the first JCUKEN dump, not this
new image. Physical timing, every printed key legend and full original
`rt1715lc` hardware operation remain unverified.

The updated [dump PR #5](https://github.com/ddanila/mame/pull/5) offers
`rt1715lc -bios jcuken` (default) and `-bios qwerty`. Byte-for-byte loading of
both selections and the default was checked in the compiled driver. This
selection check uses a synthetic host and is separate from the TOS/M test.

## Reproduce

From `emulation/`, run `python3 run.py`, `python3 analyze.py`; repeat those
commands in `emulation/language-test/`. Then run `python3 check-layout.py`
from `emulation/`. Python 3 and `/usr/games/mame` are required. Compressed raw
traces are preserved; the runners regenerate uncompressed traces.

Run `python3 verify-language-switch.py` from `emulation/end-to-end/` to check
the saved full-system evidence (requires Pillow). The Lua test is included;
use the same host ROMs and original TOS/M disk as in the
[first acquisition's reproduction instructions](../pc1715-keyboard-s642/emulation/end-to-end/README.md),
substituting this ROM for `roms/rt1715w/s600.ic8`. That filename produces an
expected S600 checksum warning. OS and host ROMs are not duplicated here.

## Programmer provenance

Willem PCB5.0E; Pocket8086 LPT 378h; DOSRAVI/CP2102 at 57600 baud.
The verified reader was uploaded as `S64QRD.COM`; commands were
`S64QRD.COM RRF5 S64QR1.BIN 378 /PROFILE:conservative` and the same command
with `S64QR2.BIN`. Execution IDs and reader SHA-256 are in the manifest.
The established 2716 setup was retained; physical rails were not independently
measured. Original stdout, session metadata and logs are in [evidence/](evidence/).
The reader rotated its previous log to `WILL0013.LOG` before read 1; read 2's
WILLEM.LOG includes both new reads. DOS clock values are not the acquisition date.
