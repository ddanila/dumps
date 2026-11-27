# Philips P2776-family terminal firmware analysis

The image is a self-contained, 128 KiB terminal firmware for the **Philips
P2776 family**, using a **NEC V25/V35-family processor**. It includes startup and
self-tests, display services, keyboard translation, serial and synchronous
interface code, several terminal emulations, multilingual setup, saved settings,
and a 512-glyph font. It is not a PC motherboard BIOS.

The strongest integrity finding is that the original ROM checksum passes when
address FFFFFh is read as the NEC IDB register (4Fh). The same routine rejects
the raw EPROM-only view and deliberate corruptions. This distinction is essential
for future emulation and for avoiding a mistaken diagnosis of a bad dump.

## Scope and evidence

Analysis date: 2026-11-27. File offsets throughout this report are hexadecimal.
The inferred physical ROM mapping is **E0000h–FFFFFh**; add E0000h to an offset
to obtain a CPU physical address. For example, file 109B2h is F000:09B2.

The report distinguishes literal bytes and executed behavior from hardware
inference. The binary has no established human-readable firmware revision or
build date. Family identification is strong; the exact terminal submodel, board
revision, CPU package and originating installation remain unknown.

Artifacts are generated from the hash-checked image:

| Artifact | Purpose |
|---|---|
| [disassembly.txt](results/disassembly.txt) | Recursive direct-flow disassembly plus documented entry points |
| [annotations.json](annotations.json) | Entry points and reasons for adding them |
| [dispatch-tables.json](results/dispatch-tables.json) | 312 literal table entries, with source and target offsets |
| [strings.json](results/strings.json) | Printable ASCII runs of at least five characters; includes false positives from data/code |
| [blocks.json](results/blocks.json) | 4 KiB entropy, padding and decoded-byte statistics |
| [io-accesses.json](results/io-accesses.json) | Decoded I/O instructions and high-offset memory operands; segment context must be checked |
| [edges.json](results/edges.json) | Direct call and branch edges |
| [execution.json](results/execution.json) | Original-code execution results |
| [font-atlas.svg](results/font-atlas.svg) | Exact glyph data rendered as an atlas |
| [comparisons.json](results/comparisons.json) | Bounded local/public comparisons |

The disassembler currently reaches **16,722 instructions occupying 42,349 unique
bytes**, including 108 instructions classified as NEC extensions. There are no
overlapping instruction starts or unsupported opcodes on these traversed paths.
This is not a claim that every executable byte has been found. The image mixes
code, strings, fonts, scripts and tables; unresolved indirect transfers are
listed in [summary.json](results/summary.json). No blanket linear sweep is used
to count data as code.

## Identification

Two strings at **11062h** and **1107Dh** name the P2776 in a video-attribute test.
The setup resources include SDI-2, RWSI, R/LWSI windows, P9000 C7/C8, OMS C7/C8,
VT52, VT100, PC TERM, host interfaces and two auxiliary devices. This combination
is much more specific than a generic VT-compatible terminal banner.

The original Philips Business Communications SOPHO iS3000 BIM manual,
[section B.2.1, printed pages 86–87](https://pt.scribd.com/document/1009813048/manual-bim-nt20),
describes a P2776 terminal with matching setup concepts, including P9000 C7,
SDI-2 and the 24+1-row display option. This supports the family attribution.
It does **not** show that this chip came from a SOPHO installation, nor does the
manual’s date establish the firmware’s date.

### Processor

The reset vector at **1FFF0h** is `EA 04 00 00 F0`: a far jump to F000:0004.
The reset entry writes **4Fh to physical FFFFFh**. Subsequent initialization
uses the register region at **4FF00h–4FFFFh** and internal RAM at 4FE00h.
Reachable code also contains NEC `TEST1`, `CLR1`, `SET1` and `FINT` instructions.
These facts identify the V25/V35 family, rather than plain 8086/8088 or 80186.

A V25 with an 8-bit external bus is plausible for a single EPROM, but the dump
alone does not establish bus wiring or the exact CPU. Ordinary modern x86
disassemblers can mislabel the NEC 0F instructions as SSE/MPX operations and
then lose instruction alignment. [analyze.py](analyze.py) handles the observed
NEC bit operations and control instructions separately and stops on unsupported
extensions.

The opcode and special-function-register interpretation was cross-checked
against the [MAME NEC implementation](https://github.com/mamedev/mame/tree/db140b2dd0bbd01a188da02cfa99b831385e3e44/src/devices/cpu/nec).
Exact source URLs and hashes are in [reference-sources.json](reference-sources.json).

## ROM layout

| File range | Contents |
|---|---|
| 00000–001FF | 512 bytes of per-glyph metadata, copied to RAM 05CAh |
| 00200–025FF | 512 packed glyphs, 18 bytes each |
| 02600–03xxx | Interrupt, serial, keyboard and support routines, interspersed with data |
| 03xxx–0705D | Keyboard/translation/protocol tables and routines; not a single homogeneous region |
| 0705E–08FE7 | Additional interface/protocol implementation, including stack-frame-based routines |
| 08FE8–0FFFF | 28,696 bytes of FF padding |
| 10000–10003 | Header: words FBBEh and E000h; the latter is the checksum start segment |
| 10004–1225E | Startup, diagnostics and controller initialization |
| 1225F–145xx | Display, window, cursor and buffer services |
| 146CF–15xxx | Configuration, interface setup and keyboard processing |
| 15xxx–17xxx | Mixed translation tables, font/character-set selection data and application code |
| 17A05 onward | Character/escape parser, with code and dispatch tables interspersed |
| 18B03–1A7xx | Multilingual setup resources, option tables and setup-related code |
| 1Axxx–1C943 | Setup helpers, terminal command handlers and trailing tables |
| 1C944–1FFEF | 13,996 bytes of FF padding |
| 1FFF0–1FFF4 | Reset far jump |
| 1FFF5–1FFFF | FF bytes in the physical EPROM |

Ranges marked `xxx` describe subsystems, not exact function boundaries. Refer
to the disassembly and tables for individual entries. No decompressor or
compressed payload was identified in the examined startup flow.

## Startup and integrity

At **10004h**, startup initially uses the NEC internal-RAM area for its stack,
relocates the internal data area using IDB=4Fh, selects SS=4000h, and calls
**11F90h** to initialize ports, wait-state/clock controls, interrupt controls and
DMA/serial state. It resets the external serial channels through ports 04h/06h,
uses the timer control register, clears 64 KiB of low RAM, and establishes
interrupt vectors and diagnostic state. Later it moves the normal stack to
0000:0400.

The retained state at segment 4000h, offset 4000h determines whether to enter
an interactive diagnostic path. The normal startup path calls **10157h** with
test-selection mask **0FDFh**, one pass, and continues to **146CFh**. The mask
selects tests 0–4 and 6–11; it does not select every external-interface test.

### ROM self-test

**109B2h** reads its starting segment from F000:0002 (E000h), visits E000h and
F000h, and adds all 65,536 little-endian words using **end-around carry**. The
expected sum is FFFFh. Failure sets bit 1 in the diagnostic mask at RAM 0082h
and stores a result at 0086h.

The physical EPROM’s end-around-carry sum is **B000h**, which looks wrong if the
CPU’s memory map is ignored. NEC reads at physical FFFFFh return the IDB register,
which startup set to 4Fh; they do not return the EPROM’s FFh. Consequently the
last CPU-visible word is 4FFFh instead of FFFFh, and the end-around sum becomes
**FFFFh**. The raw image is preserved unchanged.

Executing the original routine with Unicorn, using only this explicit IDB
memory overlay, produced:

| Input view | AX/result | Carry | Failure mask |
|---|---:|---:|---:|
| Original image, IDB=4Fh | 0000 | 0 | 0000 |
| Raw EPROM bytes, no overlay | 4FFF | 1 | 0002 |
| Original image, incorrect IDB=40h | 0F00 | 1 | 0002 |
| Bit flipped at file 00000h | FFFE | 1 | 0002 |
| Bit flipped at file 12345h | FEFF | 1 | 0002 |
| Bit flipped in reset target at 1FFF1h | FEFF | 1 | 0002 |

This validates the dump against its own integrity algorithm. It does not test
electrical behavior, the CPU or peripheral hardware.

### Diagnostics

The 16-entry table at **101CDh** dispatches the tests. The corresponding setup
labels occur at 190C0h–19228h. Test selection, repeated loops, failure recording
and an error-break option are implemented by the common dispatcher.

| Index | Entry | Test category |
|---:|---:|---|
| 0 | 108F5 | CPU/internal RAM, addressing and arithmetic/flags |
| 1 | 109B2 | ROM checksum |
| 2 | 10A09 | Memory addressing |
| 3 | 10BA8 | RAM |
| 4 | 10CB7 | Character-generator RAM |
| 5 | 10D05 | Nonvolatile memory |
| 6 | 10D4A | CRT controller |
| 7 | 10DB5 | Video/VSYNC/HSYNC |
| 8 | 11201 | Keyboard communication port |
| 9 | 113F8 | Asynchronous host communication port |
| 10 | 11BC7 | Synchronous host communication port |
| 11 | 112AB | Keyboard device |
| 12 | 11862 | Asynchronous host interface |
| 13 | 11D55 | Synchronous host interface |
| 14 | 11DEF | Auxiliary interface 1 |
| 15 | 11EB9 | Auxiliary interface 2 |

The CPU test explicitly writes 16-bit AAAAh/5555h patterns to internal RAM, tests a segment-offset wraparound case, and checks
arithmetic flags. Only the ROM checksum test was executed in the harness;
peripheral diagnostic success is not claimed.

## Memory and I/O

The code establishes these useful addresses for future emulation:

| Address/region | Evidence-based role |
|---|---|
| 00000–0FFFF | Main RAM cleared at startup; vectors, display structures, queues and application state |
| 0080 | Hardware/status word copied from retained state |
| 0082 | Diagnostic failure bitmask |
| 0084–00A3 | Sixteen per-test result words |
| 004AA / 004AC | Active display validity/index state and pointer to its descriptor pointer |
| 082ED–083FC | Runtime copy of 272 saved-setting bytes |
| 08305 | Terminal emulation selection used by parser branches |
| 08379 onward | Tab-stop array; tab scanning is bounded at column 131 |
| 0841B | Current input character |
| 0843E | CSI parameter index |
| 0843F–08454 | Eleven 16-bit CSI parameters |
| 08455 | Character-parser state |
| 08459 | Private/intermediate command marker |
| 08FF2 onward | Constructed response buffer |
| 40000–43FFF | Font expansion destination during character-generator access |
| 44025–44134 | Retained configuration block |
| 44135–44136 | Saved configuration checksum |
| 4FE00–4FEFF | NEC internal RAM after IDB relocation |
| 4FF00–4FFFF | NEC special-function registers after relocation |
| E0000–FFFFF | ROM, subject to the CPU’s special FFFFFh read behavior |

Character-generator memory access is controlled by board I/O; the destination
above is from the actual initialization sequence and is not a claim that all
board memory is always visible without banking.

| I/O port(s) | Role and certainty |
|---|---|
| 00h, 04h, 06h | External serial-controller data/control paths; programming resembles a Z80 SIO-family interface, exact device unconfirmed |
| 10h, 12h | CRT indexed data/address registers; **12634h** writes the index to 12h and word data to 10h |
| 20h, 22h | Keyboard-controller data and status/command interface; polling and 60h/C0h commands are 8042-style |
| 30h | Board/display control, including character-generator access selection |
| DX-selected ports | Additional interface/test access; preserved in the I/O inventory |

The internal serial channels are initialized at **02BB6h** and **02E34h**.
They use the NEC register groups at 4FF60h/4FF70h, install interrupt vectors,
apply baud/configuration tables and maintain receive/transmit state. Initial
flow-control words include **1311h**, the XOFF/XON byte pair. Other code supports
synchronous host interfaces; full SDI/RWSI/LWSI packet semantics are not yet
reconstructed.

## Display and fonts

The glyph loader starts at **1238Eh**. For each of 512 records starting at
file **00200h**, it reads:

1. A little-endian 16-bit bitmap supplying one extra pixel for each row.
2. Sixteen bytes supplying the other eight pixels of each row.

It emits 32 bytes per glyph to character-generator RAM: one low-byte pixel row
followed by the corresponding ninth bit. Thus **9,216 packed bytes become
16,384 bytes**. The original loader was executed through 123B4h and its entire
output was compared with the independent extractor. All bytes matched.

The [font atlas](results/font-atlas.svg) contains control-character mnemonics,
ASCII, accented Latin characters, Greek letters, mathematics, arrows, box drawing
and block graphics. Glyph IDs are shown as hexadecimal indices, not assertions
about every national encoding. The separate 512-byte block at file 00000h is
copied to RAM 05CAh; its exact per-glyph meaning is not assigned here.

Setup offers **24+1, 25 and 27 rows**. Code uses 132-column limits, and the
published P2776 configuration independently describes an 80-column mode.
Video diagnostics exercise inverse, underline, blink, highlighting, blanking,
strike-through, super/subscript and double-width/double-height text. Exact
refresh rates and the CRT controller model need hardware documentation.

Display code uses descriptors rather than a single hardcoded screen array.
The cursor service at **13A84h** bounds coordinates against descriptor dimensions
and optional scroll margins, derives visible-relative coordinates and invokes
lower-level update functions. The CSI cursor-position handler at **1B11Bh**
converts default/one-based parameters to zero-based coordinates before calling
this service. Focused execution verified zero/default parameters, normal
coordinates, oversized values, origin mode and addition overflow; it stopped
at the screen-service boundary and did not claim to render a screen.

## Terminal command processing

The main loop at **17FC9h** dispatches pending input/output and UI events.
Character handling at **17A05h** selects paths using the state byte at 8455h.
Control and printable characters use separate tables at **17A65h** and
**17A73h**. The states include normal text, ESC handling, CSI, character-set or
special-command processing, and legacy command forms.

The **32-entry C0 table at 17C30h** handles controls including BEL, backspace,
tab, line feed, carriage return, character-set shifts and ESC; many unsupported
controls return immediately. CAN and SUB reach the parser reset routine.

### CSI parser and boundaries

**17C77h** parses decimal digits and semicolons into eleven 16-bit words at
843Fh. Each digit computes `old * 10 + digit` with 16-bit wraparound. It accepts
parameter indices 0–10; an additional separator resets the parser and clears
all eleven words. Private `?` is represented by marker 1 at 8459h.

Original-code execution verified:

| Input after CSI | Observed behavior |
|---|---|
| `12;34` | Parameters 12 and 34, index 1 |
| `65535` | Parameter FFFFh |
| `65536` | Wraps to 0 |
| `99999` | Wraps to 34463 |
| `?25` | Parameter 25 and private marker 1 |
| Eleven parameters | All eleven retained |
| Separator after parameter eleven | Parser state and parameter array cleared |

The table at **17D4Bh** has 64 entries for final bytes 40h–7Fh. Execution of
all 64 dispatch cases reached the expected original handler entry. This verifies
dispatch, not the complete effects of all commands. Representative handlers:

| Final | Entry | Function inferred from code and convention |
|---|---:|---|
| `@` | 1B309 | Insert-character operation |
| `A/B/C/D` | 1B101 / 1B0F7 / 1B0FC / 1B0F2 | Cursor movement |
| `H`, `f` | 1B11B | Cursor position |
| `J`, `K` | 1B48D / 1B50C | Erase display / line |
| `L`, `M` | 1B327 / 1B322 | Insert / delete lines |
| `P` | 1B304 | Delete characters |
| `c` | 1B156 | Device attributes |
| `g` | 1C80C | Tab clearing |
| `h`, `l` | 1C3C4 / 1C3C0 | Mode set / reset |
| `m` | 1BF5A | Graphic rendition attributes |
| `n` | 1B34D | Device status reports |
| `r` | 1C6F6 | Scrolling-region handling |

The SGR handler interprets a bounded attribute table, combines set and clear
masks, and updates the current display attribute. The ROM implements additional
Philips/private and legacy commands; all extracted target values are retained
in the dispatch artifact without claiming full semantic decoding of every one.

### Actual identification and status replies

The routine at **1B156h** selects these literal replies, verified by execution:

| Emulation value at 8305h | Reply before output transport |
|---:|---|
| 0 | `ESC / Z` |
| 1 | `9B ?1;2c` |
| 2 | `9B ?62;1;2;6;8;9c` |

These are consistent with VT52, VT100 and VT220-style identities respectively.
The setup label for mode 2 is **P9000 C7**, so a VT220-style reply does not mean
the chip belongs to a DEC terminal. The routine prepares a segment:offset
pointer and length at 8437h–843Ch, and marks an outgoing response pending.
The `9B` byte is the 8-bit CSI form; these tests stop before transport conversion.

For a normal status query (`CSI 5 n`), **1B34Dh** prepares `9B 0 n` when the
diagnostic mask is zero and `9B 3 n` when it is nonzero. Both branches were
executed. This directly connects the self-tests to host-visible status reporting.

## Saved settings and setup UI

At **146CFh**, application startup validates a configuration block in retained
memory. The checksum routine **1484Fh** sums **271 bytes at 44026h–44134h**,
adds 34h to **AL only**, then adds 6132h to AX. The discarded carry from the
8-bit addition matters: this is not simply `sum + 6166h` in every case.
The result is compared with the word at 44135h.

On mismatch, startup copies 86 default bytes from **1486Eh**, initializes text
fields and a repeated four-word pattern for tab stops, writes a new checksum,
and marks the retained state. It copies 272 bytes starting at 44025h to runtime
RAM 82EDh. The checksum deliberately starts one byte after this block’s start.
The original checksum routine passed 102 independent fixtures: all zero, all
FF and 100 deterministic random blocks.

The setup resources are English at **18B03h**, German at **1963Eh** and French
around **19EF3h**. Language options are GB, D and F. Screens cover keyboard,
display, emulation, answerback and auxiliary initialization strings, tabs, host
line selection, two auxiliaries, device assignments and diagnostic selection.

Literal options include:

- VT52, VT100, P9000 C7/C8, OMS C7/C8 and PC TERM.
- SDI-2 and RWSI, with R/LWSI device windows/assignments elsewhere in the menus.
- Local echo, local/line mode, NRZ/NRZI and duplex controls.
- CTS/RTS, CTS/DTR, XON/XOFF and external flow control.
- Different baud-rate lists for different interfaces, extending to 19,200.
- National/multinational character selection and G0–G3 sets.
- Cursor style, background intensity, smooth scrolling and automatic shutdown.

These are supported menu choices, not the current configuration of the physical
terminal. Its retained RAM was not acquired, so the original user's settings
cannot be recovered from this EPROM.

## Public comparison and preservation

The saved comparison covers **69 manifest-listed local images**, two public
Philips service-processor ROMs from RetroMelsArchive, and their concatenated and
interleaved layouts. It checks exact identity, identity after trailing FF padding
removal, and contiguous-subimage matches. None matched.

The public service-processor images are explicitly from other hardware and are
not presented as P2776 revisions. The accessible Bitsavers mirror indices did
not provide a P2776 ROM/manual. A filename search of the pinned MAME source tree
found no P2776/P277x driver filename; this is not a search of all MAME ROM hashes.
No exact public match was found in this bounded investigation. A claim that this
image is unique or previously undumped would require a wider corpus.

The complete binary is preserved with its acquisition logs, manifest and
checksums. It has not been patched to make an emulator pass a checksum.

## Reproduction and validation

From the repository root, create an isolated environment, then run:

```sh
python3 -m venv /tmp/p2776-analysis
/tmp/p2776-analysis/bin/pip install -r philips/p2776/analysis/requirements.txt
/tmp/p2776-analysis/bin/python philips/p2776/analysis/analyze.py
/tmp/p2776-analysis/bin/python philips/p2776/analysis/assets.py
/tmp/p2776-analysis/bin/python philips/p2776/analysis/probe.py
/tmp/p2776-analysis/bin/python philips/p2776/analysis/compare.py --cache /tmp/p2776-reference-cache
python3 tools/check.py
```

The input image’s size and SHA-256 are asserted before analysis. Capstone and
Unicorn versions are pinned. The public comparison validates downloaded image
hashes. The local comparison changes if the repository’s corpus changes.

Focused execution covers **190 cases plus the 16 KiB font expansion**:
6 ROM-checksum scenarios, 102 configuration-checksum fixtures, 7 parser cases,
5 response cases, 64 CSI dispatch cases and 6 cursor-argument cases. The harness
executes original bytes and stops at explicit function or subsystem boundaries;
it does not silently replace terminal routines with guessed implementations.
The IDB overlay is explicit. The font loader and tested routines use the shared
x86-compatible subset, so Unicorn is not being presented as a NEC CPU emulator.

## Remaining limits and next steps

A full hardware boot has not been emulated. Timing, bank-switched memory,
keyboard behavior, interrupt bank switching, DMA, CRT operation and synchronous
host interfaces still need a board-level model. The static analysis does not
recover every indirect target or fully specify every Philips packet protocol.
No electrical checks beyond the original acquisition were performed here.

The highest-value next evidence is a board photograph showing the CPU, CRT and
serial controllers, plus the EPROM’s original paper label or a matching service
manual. With those, a MAME V25/V35-based machine model could implement the known
memory map, IDB behavior, indexed CRT ports and keyboard interface, then progress
through the existing self-tests to a rendered setup screen. Until then, the
report and executable probes establish firmware identity, integrity and major
behavior without claiming a successful machine boot.
