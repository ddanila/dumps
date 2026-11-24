# Puritan Bennett 7200 MEGACPU EPROMs

Owner reports nine EPROM positions numbered 0 through 8, with chip 7
missing. All eight available chips (0–6 and 8) have now been read twice and preserved.
The ROM set remains incomplete because chip 7 is missing.
Board reference: owner photo `133870106.jpg` (not in the repository).
Chip 0's socket designation and full sticker text are not yet confirmed.
Other visible ROMs carry `26300-85-V`; that label is not assigned to chip 0
without a readable photograph or independent evidence.

## Firmware analysis and emulation

The [firmware investigation](analysis/README.md) includes a reproducible 16-bit
x86 execution harness, seven recorded experiments, a feature inventory, observed
call/read references, and a [searchable catalog of 2,856 printable runs](analysis/catalog/strings.html).
Original code reaches application startup, scheduler/serial activity and fault
message formatting under documented peripheral mocks. Normal operation is not
emulated; chip 7 remains missing and was not accessed by these paths.

## Chip 0 acquisition

Read twice on 2026-11-14 with T48 firmware 00.1.03, minipro 0.7.4:

```sh
minipro -p M27512@DIP28 -x -r OUTPUT.bin
```

Both operations exited zero and produced identical 65536-byte captures.
ID probing was disabled; no programming or erase command was issued.
The profile specifies 5 V read/verify voltage, not an independently measured
chip-rail value. Minipro reports incomplete T48 support and firmware older
than expected. Original logs and metadata are in `evidence/`; both raw
reads remain in the session path recorded in `manifest.json`.

The chip is provisionally treated as a standard-pinout 28-pin 27-series
EPROM, per the owner's description. Exact physical type and capacity are
unconfirmed. CRC32 of the complete unmodified capture is `bc8a5f28`.

## Initial content inspection

The lower 32 KiB is entirely `CC`. The upper 32 KiB contains code-like bytes,
diagnostic text and more CC-filled regions. The image does not repeat at
2, 4, 8, 16 or 32 KiB boundaries. This does not establish 64 KiB physical
capacity: a smaller device may have different control/supply pin functions
under this provisional profile. No padding has been stripped.

Readable text includes `Q1 PROM ERROR`, `Q2 PROM ERROR`, `MULTIBUS RAM ERROR`,
`ADC     OUT OF TOLER`, `BUV IS ON`, `LOW  AC  POWER`, and `SETUP ERROR`.
At offset `fff0`, bytes `ea 00 00 c0 ff` decode as the 16-bit x86 far jump
`JMP FFC0:0000`. If mapped at the top of the first MiB, that targets offset
`fc00` in this image, where the byte stream begins with plausible I/O-port
initialization instructions. Together these observations strongly suggest
boot/power-on-self-test firmware, unlike the Q1–Q3 sensor data ROMs.
No execution or full disassembly has been performed in this acquisition.

The manufacturer's [parts list](https://doczz.net/doc/2483138/puritan-bennett-7200)
identifies the MegaCPU as 80188-based, consistent with the x86 reset sequence.
Public searches by capture SHA-256, CRC32 and system name found no matching
downloadable dump. Internet uniqueness is not established.

## Chip 1 / U304: 26300-85-V

Read twice on 2026-11-14 with the same T48 and provisional `M27512@DIP28`
profile, ID probing disabled. Both reads exited zero and match exactly.
The unchanged capture is 65536 bytes, CRC32 `894e6c09`, and includes all
256 byte values. It does not repeat at 2, 4, 8, 16 or 32 KiB boundaries;
physical chip type and capacity remain provisional.

The overview photo identifies the sticker as `1 U304 / 26300-85-V`. The
capture contains the matching ASCII identifier `26300-85-V`, model strings
`7200e`, `7200spe`, and `7200ae`, and `19951018080000`, plausibly a build
timestamp of 1995-10-18 08:00:00 (interpretation not independently verified).
There are extensive keyboard prompts, self-test and display messages,
including `PUSH ALRM RESET`, `INVALID KEY`, `CONNECT AIR`, `CONNECT O2`,
`EST PASS`, `EST FAIL`, and a message about turning off trending before
accessing a results screen. Printable runs and offsets are saved in
`evidence/chip1-strings.json`. This is part of the application ROM set;
no execution or complete code/data classification has yet been performed.

[Fukuda's DS-7200 maintenance manual](https://www.fukuda.co.uk/products/sitefiles/DS-7200_MAINT_4L010032C_CE.pdf)
independently lists `26300-85-V` as a PB7200 software version. Public searches
by this version and the capture hashes found documentation but no matching
downloadable ROM candidate. This does not establish Internet uniqueness.

## Chip 2 / U305: 26300-85-V

Read twice on 2026-11-14 with the same T48 and provisional `M27512@DIP28`
profile, with ID probing disabled. Both operations exited zero and the
65536-byte captures match exactly. CRC32 is `b4257daa`; 250 distinct byte
values occur, and the capture does not repeat at 2, 4, 8, 16 or 32 KiB
boundaries. Physical chip type and capacity remain unconfirmed.

The overview sticker reads `2 U305 / 26300-85-V`. The image begins with
extensive display text, including compliance and resistance measurements,
inspiratory pressure, vital capacity, waveform ranges, trending, cursor
movement and printing prompts. For example: `PRESS ALARM RESET TWICE TO
ABORT PRINTING` and `ACCESS FUNCTION 61 TO CHANGE OR EXIT TRENDING`.
The last 64 bytes are CC-filled. This is another component of the
application ROM set; no complete code/data classification or execution has
been performed. Printable runs and offsets are in `evidence/chip2-strings.json`.

Public searches by SHA-256, CRC32 and version/socket found no downloadable
matching candidate. This does not establish Internet uniqueness. Full raw
bytes and original read evidence are retained unchanged.

## Chip 3 / U404: 26300-85-V

Read twice on 2026-11-14 with the same T48 and provisional `M27512@DIP28`
profile, ID probing disabled. Both operations exited zero and the complete
65536-byte captures match. CRC32 is `a9790c64`. All 256 byte values occur;
there is no repetition at 2, 4, 8, 16 or 32 KiB boundaries. These results
establish repeatability, not physical chip type or capacity.

The overview sticker reads `3 U404 / 26300-85-V`. This capture contains much
less readable text than chips 1 and 2: the printable-runs extraction finds
an alphabet/digit sequence and strings such as `010185  1200  20.90`, plus
incidental printable bytes. The numeric text has not been assigned a date,
unit or other meaning. Much of the image looks consistent with binary
code/tables, but no full disassembly or execution has been performed.
Printable runs and offsets are preserved in `evidence/chip3-strings.json`.

Public searches by capture SHA-256, CRC32 and version/socket returned no
matching candidate. This does not establish Internet uniqueness. Original
read logs, metadata and the full unmodified capture are retained.

## Chip 4 / U405: 26300-85-V

Read twice on 2026-11-14 with the same T48 and provisional `M27512@DIP28`
profile, with ID probing disabled. Both operations exited zero; the complete
65536-byte captures match. CRC32 is `053e5563`. All 256 byte values occur,
and there is no repetition at 2, 4, 8, 16 or 32 KiB boundaries. Physical
chip type and capacity remain unconfirmed.

The overview sticker reads `4 U405 / 26300-85-V`. Alongside binary content,
the image contains comma-separated record templates with prefixes including
`PD`, `AL`, `AS`, `VS`, `ER`, `BBR`, `PID`, `PCV`, `VSR` and `EST`. These
suggest formatted reporting/communications data, but their exact meanings
and use have not been traced. There is also `PURITAN-BENNETT` text. No full
code/data classification or execution has been performed. Printable runs
and offsets are preserved in `evidence/chip4-strings.json`.

Public searches by capture SHA-256, CRC32 and version/socket returned no
matching candidate; Internet uniqueness is not established. Original read
logs, metadata and the unmodified full capture are retained.

## Chip 5 / U505: 26300-85-V

Read twice on 2026-11-14 with the same T48 and provisional `M27512@DIP28`
profile, ID probing disabled. Both operations exited zero and produced
identical 65536-byte captures. CRC32 is `7e6a4983`. All 256 byte values occur;
there is no repetition at 2, 4, 8, 16 or 32 KiB boundaries. Physical chip
type and capacity remain unconfirmed.

The overview sticker reads `5 U505 / 26300-85-V`. The image has relatively
little readable text: extracting printable runs of at least eight bytes
finds 11 runs, including comma-separated templates beginning `TIME,` and
`VCHG,`. Most of the capture is binary content consistent with code/tables;
no complete disassembly or execution has been performed. Printable runs
and offsets are saved in `evidence/chip5-strings.json`.

Public searches by capture SHA-256, CRC32 and version/socket returned no
matching candidate. Internet uniqueness is not established. The full raw
capture and original acquisition evidence are preserved.

## Chip 6 / U506: 26300-85-V

Read twice on 2026-11-14 with the same T48 and provisional `M27512@DIP28`
profile, with ID probing disabled. Both operations exited zero and the
65536-byte captures match exactly. CRC32 is `a6cc92b3`. All 256 byte values
occur; no repetition was found at 2, 4, 8, 16 or 32 KiB boundaries. Physical
chip type and capacity remain unconfirmed.

The overview sticker reads `6 U506 / 26300-85-V`. No runs of eight or more
printable ASCII bytes were found; this does not exclude shorter text or
other encodings. The image contains binary content consistent with code
and ends in CC-filled bytes. No complete disassembly or execution has been
performed. The empty printable-runs result is recorded in
`evidence/chip6-strings.json`.

Public searches by capture SHA-256, CRC32 and version/socket returned no
matching candidate. Internet uniqueness is not established. The full raw
capture and original acquisition evidence are preserved.

## Chip 8 / U606: 26300-85-V

Read twice on 2026-11-14 with the same T48 and provisional `M27512@DIP28`
profile, ID probing disabled. Both operations exited zero and produced
identical 65536-byte captures. CRC32 is `0c039250`. All 256 byte values occur;
there is no repetition at 2, 4, 8, 16 or 32 KiB boundaries. Physical chip
type and capacity remain unconfirmed.

The overview sticker reads `8 U606 / 26300-85-V`. The image starts with
repeated alphabet/digit strings (`ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789`).
The printable-runs extraction finds 11 runs of at least eight bytes; later
runs include short labels such as `EST`, `ALARM` and `PTRND` alongside other
printable bytes. These local string repetitions do not make the whole ROM
a repeated smaller image. The final 64 bytes are CC-filled. No complete
code/data classification or execution has been performed. Printable runs
and offsets are saved in `evidence/chip8-strings.json`.

Public searches by capture SHA-256, CRC32 and version/socket returned no
matching candidate. Internet uniqueness is not established. The complete
raw capture and original acquisition evidence are preserved.

## Acquisition status

All eight present EPROMs have two matching reads, each preserved as a raw
64 KiB capture (512 KiB total). Chip 7/U605 is physically absent and has
not been reconstructed or replaced by a fabricated image. Repeatability
and the coherent text/code observations do not establish an executable
complete set or confirm the physical device types.
