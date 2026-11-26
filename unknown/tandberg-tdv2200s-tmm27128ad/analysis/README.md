# TMM27128AD-20 terminal ROM analysis

This image is an **8085 program linked at 0000h**, strongly attributable to the
**Tandberg TDV-2200S firmware family**. It contains the primitive service layer
and the beginning of a larger terminal application. It is not a character
ROM or a standalone keyboard ROM. The exact model, release number, original
label and board socket remain unknown.

Analysis uses the unmodified [16 KiB image](../tmm27128ad-20.bin), SHA-256
`739c871b383c216428ee833d2758b7590ab4e589b76a065dece91e532cfb1849`.
No missing ROM bytes were synthesized. Findings below distinguish direct code
observations, isolated execution results and hardware-family inference.

## Identification and integrity

The reset vector is `DI; JMP 01E8h`. Hardware interrupt entry points at 002Ch,
0034h and 003Ch agree with 8085 RST 5.5/6.5/7.5. The reachable initialization
instruction at 0914h is **SIM** (30h), and video routines use **RIM** (20h) to
poll bit 7. A Z80 decoder incorrectly consumes following instructions as
relative-branch operands at these locations. This is why the preserved listing
uses an 8085-aware decoder.

The public TDV-2200S image `965090-24 -1-.27128.u93` starts with the same 65
bytes. Long identical spans include 051Fh–05FFh (225 bytes), 026Dh–0307h
(155 bytes), 0381h–0417h (151 bytes), and 0454h–04D7h (132 bytes). The common
reset and interrupt layout, primitive API, serial initialization and display
handling provide substantially stronger attribution than the menu text alone.
The reference differs at 13,771 aligned byte positions; it must not be used as
a byte-for-byte replacement or as an assumed source for missing addresses.

[comparison.json](comparison.json) records 19 public images, their pinned
URLs and SHA-256 hashes, exact/embedded/word-swap checks, aligned comparisons
and longest matching blocks. The 7,941 ordered matching bytes reported by
`difflib.SequenceMatcher(autojunk=False)` are a similarity metric, not a patch
map or proof that all of those bytes represent equivalent instructions.
The 97 local `.bin` comparisons also found no exact/embedded match.

There are 16,310 non-FF bytes and 74 FF bytes. Every address bit A0–A13
separates differing contents; no whole-image address-line mirror was found.
The byte sum is 59h modulo 256, or 2559h modulo 65536. These are descriptive
sums, **not an independently verified firmware checksum**. The ROM's own
checksum test takes its ranges from nonvolatile descriptors and expects an
aggregate AAh; those descriptors and the rest of the firmware are unavailable.

## ROM structure and analysis coverage

| Addresses | Role |
|---|---|
| 0000–003F | Reset, restart and interrupt entry stubs |
| 0040–01E3 | 140 consecutive three-byte JMP service entries |
| 01E4–0289 | Common return stub, reset, module selection, error text |
| 028A–065E | Interrupt dispatch, serial/keyboard/printer service, software timers |
| 065F–0906 | RAM, display, serial, keyboard and ROM self-tests |
| 0907–0EB2 | Service initialization and communication/control APIs; includes tables |
| 0EB3–101B | Circular queues, including optional large printer queue |
| 101C–1175 | Nonvolatile-memory access and configuration packing/unpacking |
| 1176–19DE | Cursor, display, scrolling, attributes and setup-related primitives |
| 19DF–1E81 | Menu helpers, PUSH-key editor, string and conversion helpers |
| 1E82–20EB | Coordinate checks, display addressing, formatting, attributes/control |
| 20EC–20FF | Padding/metadata-like bytes; purpose not fully identified |
| 2100–2101 | Application signature `80 80` |
| 2102–25BE | Application setup/event loop, keyboard/host dispatch |
| 25BF–26BE | Four 32-entry address tables |
| 26BF–3FFF | Control/escape handling, editing, backing-store and output routines |

The [recursive disassembly](disassembly.asm) accounts for **15,584 bytes
(95.12%) in 7,891 decoded instructions**, with no overlapping decoded
instructions. The remaining 800 bytes are emitted as `DB` and include pointer
tables, strings and unclassified bytes. Coverage means reachable from the
explicit seeds and direct branches used by the analyzer, not that every byte
has been semantically understood or exercised. Conditional paths are explored
both ways; indirect destinations require explicit evidence-based seeds.

The [API table](api.tsv), [control tables](control-dispatch.json),
[direct call/jump edges](edges.json), [symbols](symbols.json),
[I/O accesses](ports.json) and [statistics](static.json) are machine-readable.
Symbol names describe recovered behavior; they are not original source labels.
[Printable runs](strings.json) include accidental instruction-byte strings and
must not all be interpreted as user-visible text.

## Reset, module selection and diagnostic behavior

1. Reset disables interrupts, writes board controls, initializes CRT registers
   30h–36h, clears several CRT-control ports, and sets SP to 5FFFh. The exact
   first 14 port writes are reproduced in [probe-results.json](probe-results.json).
2. It checks bytes at 8000h/8001h. A module signature is accepted when their
   addition produces zero **with carry**, meaning their ordinary sum is 100h.
   `80 80` passes; `00 00` does not. An accepted expansion module is initialized
   through the local service layer and entered at 8002h.
3. Otherwise it inspects a warm-start marker at 5E0Ch. An invalid marker leads
   to the cold diagnostic suite at 065Fh. Service initialization is at 0907h.
4. A diagnostic failure prints `ERROR NO.:` from 027Fh and a hexadecimal error
   byte through 1F5Bh. The following keyboard-command loop retries transmission
   of 18h until the interface accepts it.
5. Startup stores `8080h` at 5E0Ch, then tries module headers at 2100h and C000h.
   The local `80 80` at 2100h selects application entry 2102h. If neither
   candidate is accepted, it displays `???` and loops at 026Eh.

The local application begins with `JC 2102h`: it deliberately waits forever
when entered with a set carry (diagnostic failure). Successful entry continues
at 2105h. This is meaningful failure handling, not an accidental self-branch.

### Self-tests

| Routine | Verified static behavior / error code |
|---|---|
| 0702 | Write/read low address bytes, then high address bytes; clear tested range; carry indicates mismatch |
| 06DC | Validate descriptor endpoints, then test RAM-designated ranges; 1Ah for invalid descriptor markers |
| 069B / 06C0 | Sum ROM-designated ranges modulo 256 into 5E01h; expect AAh, otherwise 19h |
| 0777 | Write/read display characters and their attribute latch; 0Fh character failure, 11h attribute failure |
| 07D5 | Serial control/loopback tests with 55h and 2Ah; errors 12h, 13h, 14h |
| 0891 | Keyboard commands 2Dh/2Eh or 81h/82h, expect AAh replies; errors 15h–18h |

Descriptors are read via the nonvolatile-memory API at offsets 50h–5Fh.
Each descriptor pair gives a type/size and a starting page. The low five
size bits become a length in 1 KiB units; type bits 80h identify ROM and 40h
identify RAM. The execution probes confirm the additive accumulator and show
that the original RAM test detects an injected read-bit error. They do not
claim the original terminal's peripherals passed these diagnostics.

## Hardware and RAM map

The firmware's port accesses agree with the first-hand
[Tandberg memory/I/O reconstruction](https://github.com/Supermagnum/Tandberg/blob/main/TDV-2200/Terminal%20Mem%20IO-map.txt).
Component identities below are supported by that hardware source as well as
the programming patterns; they are not read from an embedded manufacturer
banner.

| Ports | Recovered use | Hardware association |
|---|---|---|
| 00–03 | Two data/control channel pairs, register-select writes | Z80 SIO serial controller |
| 10–11 | Status/control then keyboard data | MC6850 keyboard ACIA |
| 18–19 | Second status/control/data pair | MC6850 printer ACIA |
| 20–23 | Counter words and control bytes 36h, 76h, B6h | 8253 timer |
| 30–3F | CRT timing, scroll/cursor control | TMS9937/CRT5027 family |
| 50 | Cached control byte at 5E10h; includes nonvolatile-memory selection | Board control 1 |
| 60 | Cached control byte at 5E0Eh and status reads | Board control 2 |
| 70 | Character attributes accompanying video-memory accesses | Attribute latch/plane |

The Z80 SIO is a peripheral; its presence does not make the processor a Z80.
RIM polling on video accesses is specific evidence for the 8085 host CPU.

| Memory | Evidence and use |
|---|---|
| 0000–3FFF | This physical EPROM |
| 4000–57FF | Missing continuation code and resources; direct calls and installed callbacks point here |
| 5800–5BFF | Application state, backing-store indexes and row map |
| 5C00–5C0B | Three countdown words and callback-pointer pairs |
| 5C10–5C2D | Interrupt/event callback words |
| 5C2E–5DEF | Communication queues and state |
| 5DF0–5DFF | Large-queue indexes, flags and configuration pointers |
| 5E00–5EFF | Primitive-layer state, cursor, board controls and menu scratch |
| 5F00 onward | Unpacked configuration values; stack initialized at 5FFFh |
| 6000–78xx | Display character pages, 80 active columns per 256-byte page |
| 6000–65FF, selected mode | Nibble-oriented nonvolatile-memory windows; overlaps display decode |
| 8000 onward | Expansion/backing RAM or optional module, depending on configuration |

The local application installs callbacks at 4771h, 47EBh, 4824h, 4832h, 4853h,
485Ah and 4861h, and switches its configuration template to 4D99h. These are
outside this capture. The final byte at 3FFFh is an instruction (`DCR B`),
with a reachable fall-through to 4000h. The image size is the chip's full
capacity; the absent continuation is not an acquisition truncation.

## Serial I/O, keyboard and queues

Initialization selects SIO registers 1, 3, 4 and 5, derives parameters from
configuration bytes at 5F00h onward, and programs timer divisors. The
[12-entry divisor table](baud-divisors.json) at 0B2Fh is:

`2304, 1536, 1047, 856, 576, 384, 192, 96, 48, 24, 12, 6`.

The ratios are consistent with a baud-rate table. Absolute baud labels require
the clock and SIO multiplier setting; they are not assigned from ratios alone.
The table-selector routine at 0B24h has been executed for all 12 valid indexes.

The keyboard transmit primitive at 0CE6h tests bit 1 of port 10h. If ready,
it writes the command to 11h and clears carry; otherwise it sets carry without
writing. Both paths were executed. Wrappers send fixed commands including
24h for the bell path. Receive service uses the queue at 5D9Dh and carries
internal key codes, not just ASCII.

The generic 32-byte queues maintain a count, write index and read index.
Carry reports full/empty. The serial receive queue has 256 physical slots but
caps occupancy at 255. The small printer queue can be replaced by a 2,000-byte
queue based at the RAM pointer in 5DFFh when 5DFEh is nonzero.

| Enqueue / dequeue | Data base | Metadata base | Capacity |
|---|---|---|---|
| 0EEF / 0EFB | 5D9D | 5DBD | 32, keyboard |
| 0F06 / 0F12 | 5D31 | 5D53 | 32, serial transmit |
| 0F1D / 0F29 | 5D79 | 5D9A | 32, second serial transmit |
| 0F34 / 0F4B | 5C2E | 5D2E | 255, serial receive |
| 0F61 / 0F6D | 5D56 | 5D76 | 32, second serial receive |
| 0F78 / 0F8F | 5DE4 | 5DEC | 8, auxiliary queue |
| 0FA5 / 0FE3 | 5DC0 or pointer at 5DFF | 5DE1 or 5DEF–5DF4 | 32 or 2,000, printer path |

All seven queue pairs pass ordered fill/drain, full rejection, empty detection
and repeated wrap tests. The optional large queue also passes two full cycles.
The auxiliary queue's physical role is left unassigned.

## Display, attributes and backing store

Coordinates are one-based: H is row 1–25, L is column 1–80. Routine 1E82h
validates them and returns carry on invalid input. All 65,536 possible HL
values were tested. Cursor state is at 5E16h. `124Dh` validates before setting
it, while `1251h` sets it directly.

The primitive display maps each row to one 256-byte page, using columns 00h–4Fh.
The row offset at 5E1Ah provides circular scrolling. Traversal wraps after
784Fh to 6000h; reverse traversal wraps back. Both directions were tested at
all 2,000 active cells. Video memory accesses are paired with port 70h attribute
accesses and RIM/SID polling; synthetic RAM alone cannot reproduce that bus.

The application has a separate packed backing-store layout. `3E45h` obtains a
row number from the table at 5B00h and multiplies its zero-based index by 120,
adding the base pointer at 58ABh. `3E71h` advances three bytes for each pair of
columns. Companion routines select the two characters and low/high attribute
nibbles. This is consistent with 80 characters plus 40 attribute bytes per row.
The attribute-bit meanings and all application modes are not fully resolved.

## Nonvolatile settings and PUSH keys

`101Ch` reads one logical byte from two physical four-bit cells separated by
0200h. `108Ch` accepts logical addresses 0000h–01FFh and maps them into the
6000h window. Control-port bit 2 selects the window. `1050h` splits a byte
into nibbles, and `1098h` performs the erase/write-delay/readback sequence.
Those delays are software loops, not evidence of an exact wall-clock duration.
This matches the family's ER3400-style nonvolatile storage organization.

`10E6h` unpacks 11 stored bytes according to a bitfield template, writing
individual settings beginning at 5F00h. `112Ah` packs settings back. The local
primitive template is at 099Dh; the application replaces it with a template
at 4D99h in the missing continuation. Consequently the complete list of menu
labels, settings and their enumerations cannot be recovered from this chip.

The editor at 1B35h displays `PUSH-KEY MENU` and `HEX CODE : `. Its 16 logical
slots have the following capacities and nonvolatile offsets:

| Slots (one-based) | Capacity per slot | Starting offsets |
|---|---|---|
| 1–8 | 12 bytes | 0060, 006C, 0078, 0084, 0090, 009C, 00A8, 00B4 |
| 9–12 | 32 bytes | 00C0, 00E0, 0100, 0120 |
| 13–16 | 48 bytes | 0140, 0170, 01A0, 01D0 |

The capacities total 416 bytes and end at 01FFh. This matches the capacity
scheme described in the manufacturer
[TDV-2200/9 user's guide, section 6.3](https://lastin.dti.supsi.ch/VET/vts/TDV-2200/TDV-2200_9-User-s_Guide-ND.pdf).
The manual describes shifted/unshifted PUSH keys; the dump proves the logical
slot layout, without establishing this loose chip's physical keyboard legends.

The edit loop recognizes DBh as exit, CEh as hex input, CFh as literal input,
B1h/B2h as previous/next slot, B3h/B4h as next/previous character and B8h as
first slot. Capacity and address selection were executed for every 8-bit input
(including rejection or low-nibble masking outside the normal range).

The hex-input path is not a strict ASCII-hex parser: inspection of 1F9Ch shows
that values between `9` and `A` are not all explicitly excluded before the
second subtraction. Treat its behavior as historical input handling, not a
modern validated conversion API. No security conclusion is implied.

## Application control and escape sequences

The event loop starts at 229Eh and dispatches through RAM-held pointers.
Host-byte handling at 2553h separates ordinary characters, C0 controls and
80h–9Fh controls. The indirect dispatcher at 258Eh uses `2 * (A & 1Fh)`.
Four tables at 25BFh, 25FFh, 263Fh and 267Fh cover controls and internal keys.
They contain 128 entries, including repeated targets at 26BFh (`RET`).

Recovered examples:

| Input | Handler | Behavior |
|---|---|---|
| 07h BEL | 292D | Retry keyboard-bell primitive until accepted |
| 08h BS | 2E0D | Backspace with mode/field-boundary handling |
| 09h HT | 2EFA | Horizontal tab handling |
| 0Ah LF | 295B | Advance line, with scrolling dependencies |
| 0Dh CR | 2947 | Move to column 1; configurable LF behavior |
| 0Eh SO / 0Fh SI | 2977 / 2972 | Set/clear the 80h character-bank flag at 5863h |
| 1Bh ESC | 29B6 | Escape interpreter |

The escape interpreter recognizes `ESC c`, `ESC #`, and final bytes 40h–5Fh
routed through the 25FFh table (with 5Dh excluded). `ESC # 5/6` paths manipulate
line-format attributes. Further parsing at 2B27h/2B41h selects tables 263Fh and
267Fh. The application includes field-oriented editing, scrolling, character
classification and print/output paths. These observations do **not** establish
complete VT100/ANSI conformance: many handlers and output routines call missing
4000h–57FFh code, and mode-dependent behavior needs the rest of the set.

## Executed checks, limits and reproduction

[probe.py](probe.py) compiles a pinned MIT-licensed 8080 core from
[ddanila/dac-emulation](https://github.com/ddanila/dac-emulation/tree/2e57421095e18337e5b65bf2505d8f0f012766dd/third_party/cpu/i8080),
checks its source hashes, and runs the original ROM bytes through a small
[bridge](probe_bridge.c). It rejects all 8085-only/8080-undefined instructions,
execution outside this image, reads from the missing continuation, writes below
5800h, and input ports not supplied by a case. No missing function is replaced
with a successful return. Registers, RAM, stack and the explicitly exercised
keyboard status input are synthetic.

The 80,909 cases cover reset's initial port programming, every coordinate,
forward/backward display traversal, queue boundaries and wrapping, PUSH-key
lookup/capacities, divisor selection, all 256 decimal conversions, four checksum
ranges, RAM-test success/fault, and keyboard transmit ready/busy. Test counts
include parameterized cases and queue operations, not distinct hardware scenarios.
The probes intentionally stop short of a full 8085 boot and do not validate
interrupt timing, CRT signals, physical serial traffic, EAROM retention or
operation of the original board.

From the repository root:

```sh
python3 unknown/tandberg-tdv2200s-tmm27128ad/analysis/analyze.py
python3 unknown/tandberg-tdv2200s-tmm27128ad/analysis/probe.py
python3 unknown/tandberg-tdv2200s-tmm27128ad/analysis/compare.py --cache /tmp/tandberg-reference-roms
python3 tools/check.py
```

Static analysis uses only Python's standard library. Probes require a C compiler
and network access to fetch the pinned CPU source into a temporary directory;
`--cpu-source PATH` can use an existing checkout with the same hashes. Public
comparisons use a user-selected external cache. The `.bin` file and raw reader
logs are never modified by these scripts. Local comparison counts can change
as other sets are added to the repository.

To advance beyond this analysis, the useful missing evidence is the board's
4000h–57FFh firmware, its character generator, saved nonvolatile contents,
and photographs/labels establishing the exact model and revision. The present
capture establishes the family and major subsystems, but cannot supply those
missing resources or uniquely identify a complete terminal configuration.
