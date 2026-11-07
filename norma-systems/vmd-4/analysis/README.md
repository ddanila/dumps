# VMD-4 firmware: parallel flash use

Static analysis, 2026-11-07. Input is the preserved single-read 27C512 image,
SHA256 `40ac0caceb2576887a4d6cbf710258689c3d200711f26cfaa90492db1d5ea386`.
This is strong evidence that the board uses a parallel flash for persistent
data, including an access code. It does **not** validate the AT29C512 read3
capture or identify every function of the video device.

## CPU and address spaces

The EPROM contains 8051-family instructions. SFR use matches Siemens C509-L:
SYSCON B1, SYSCON1 B2, WDTREL 86, DPSEL 92, P4 E8, P5 F8, P9 F9, P6 FA.
This is a firmware-based identification, not a visual reading of the CPU label.
Startup writes SYSCON=A0, enabling XRAM on that MCU. FF00 and FF80 are RAM
buffers; they must not be mistaken for flash chip addresses. The C509-L has
internal XRAM at F400..FFFF, accessed using MOVX instructions.
[Siemens C509-L datasheet](https://www.phytec.de/fileadmin/user_upload/C509-L_ds.pdf).

## Flash interface recovered from instructions

| EPROM code address | Behavior |
| --- | --- |
| 03E4..0409 | Read 128 bytes through port F9 into the RAM buffer at DPTR |
| 03A0..03E3 | Write bytes from RAM through F9, delay, then compare the last byte against repeated reads (up to 80 attempts) |
| 0133..0148 | Read page 1C3, copy offsets 04..09 into internal RAM 45..4A |
| 0425..0447 | Check six incoming bytes against those saved bytes, with a ROM fallback per character |
| 0449..047F | Replace the six bytes and write the containing page back |
| 0314..039B | Update four pairs of pages plus ten bytes in page 1C3 |
| 0A40..0A70 | Read/modify/write page 1D0 using a seven-byte incoming record |

The write routine takes its count in R1 and byte offset in R7; the listed
callers pass 128 and zero. Read initializes those itself. Each byte's address
is constructed as follows:

```text
P4[6:0] = R7[6:0]
P4[7]   = internal RAM[39h] bit 0
P5[6:0] = internal RAM[39h] bits 1..7
P5[7]   = bit-address 34h (internal RAM 26h bit 4)
```

Assuming the natural P4/P5-to-address wiring, the flash address is
`(bit34 << 15) | (RAM[39h] << 7) | R7`. Physical address/data bit order remains
unverified without tracing the board. P9 carries data; P3.4, P3.5 and P1.7
control the transfers. Exact assignments to /CE, /OE, /WE or intervening
buffers cannot be proved from software alone.

The 128-byte write and last-byte polling closely match the AT29C512's
512 sectors of 128 bytes and program-completion polling. This is a strong
identification of the interface, not proof of which physical socket it reaches.
Normal reads need no unlock sequence; software data protection controls
programming. [Atmel AT29C512 datasheet](https://www.allelcoelec.pt/datasheets.26/AT29C512-15JI.pdf).

## What data is stored

Under that address interpretation, boot reads E180..E1FF and copies
**E184..E189** into six bytes used to authorize an update. The ROM fallback
characters are `Tracy ` (including a trailing space), selected in reverse
order from code offsets 0109..0104. Each incoming character may match either
the stored byte or the corresponding fallback byte; it is not a separate
whole-string comparison. Calling this an access code/password is an inference
from the comparison and update behavior.

The block-update path changes the last four bytes of pages beginning at
**A900, B900, C900, D900**, followed by the first 55 bytes of the respective
next pages **A980, B980, C980, D980**. It then updates ten bytes at E180.
Thus the firmware deliberately stores meaningful data at page ends.

Another path updates seven bytes at a 16-byte-aligned offset in the staging
buffer for page **E800**. The offset is `(incoming_byte & 15) * 16`, but only
the first 128 buffer bytes are written back. Do not infer sixteen persistent
slots: incoming indices 8..15 fall outside that writeback region. Record
semantics and valid command arguments have not yet been established.

These routines establish persistent data storage, not execution of code from
the flash. They do not exclude other uses elsewhere in the firmware.

## What this means for the current capture

Read3 SHA256 is
`68568fe682e451dc8166761c658522c527bd2187d14285c4c5bab0b249ea204c`.
It has 64742 FF bytes, 732 04 bytes, and 62 06 bytes; all non-FF bytes occur
at offsets 125..127 within a 128-byte page. Every page contains a non-FF byte.
The inferred six-byte access code and the beginnings of the named data pages
are all FF. That neither proves corruption nor confirms sensible config:
unused/uninitialized settings remain possible, and the ROM fallback can
permit an access-code update even with erased stored bytes.

Earlier suspicion based on 128-byte spacing alone was too strong. Page size
and page-end storage are now supported by the firmware. However this single
corrected read cannot establish whether its 04/06 values are real. The first
two captures used the confirmed wrong /WE level and are not validation reads.
No second reader defect has been established by this firmware analysis.

A useful next hardware experiment is a small read-only selection of these
pages in different address orders, including repeated individual addresses
around page boundaries. Compare against read3 before another full acquisition.
This could expose history-dependent sampling; identical results would improve
confidence but would not independently prove the electrical interface correct.
No additional physical read or write was performed for this analysis.

## Reproduction

`analyze_flash.py` checks the EPROM hash, generates Intel HEX for dis51 0.5, and
optionally summarizes a local diagnostic flash capture. Run:

```sh
python3 analyze_flash.py --hex /tmp/vmd4.hex --flash /path/to/VMD29R3.BIN
dis51 -l 0 3 11 19 27 35 < /tmp/vmd4.hex > /tmp/vmd4.asm
```

The relevant listing is preserved in `flash-excerpts.asm`. Inspection is
static; no MCU emulator, actual board execution, or physical wiring validation
is claimed. Raw diagnostic captures remain in the DOSRAVI session directory
recorded in ../at29c512/README.md.
