# Code analysis — unidentified set 41–44

Analysis date: 2026-09-07. Static analysis only; no firmware boot, live I/O,
hardware test, or writes to the original ROM images were performed.

## Summary and confidence

- **High confidence:** 8080-compatible code; sequential ROM order 41, 42, 43,
  44; signed decimal message construction/parsing; packed-BCD arithmetic;
  bidirectional peripheral data transfers. All four internal additive ROM
  checksums pass in this order.
- **Strong inference:** an IEEE-488/GPIB-style addressed talker/listener,
  likely part of a programmable instrument. The evidence is the bus-command
  decoder and its connection to the actual message-transfer paths, not just
  isolated constants or printable bytes.
- **Unresolved:** original system, CPU part number, measured/controlled
  quantity, command-letter meanings, exact peripheral chips, connector and
  electrical interface. Instrumentation is a stronger hypothesis than before,
  but not grounds to rename the set after a specific device.

## ROM arrangement and integrity

Concatenate whole chips; do not interleave their bytes:

| Label | PCB position | Inferred CPU address / combined offset |
|---|---|---|
| 41 | 4 | `0000–07FF` |
| 42 | 3 | `0800–0FFF` |
| 43 | 2 | `1000–17FF` |
| 44 | 1 | `1800–1FFF` |

Combined SHA-256:
`b12fd392ea3a49fdd507e8c61decfe2f5972c3c1b7b9aec51455a329548c00b8`.
These addresses follow absolute code references and assume the natural
zero-based mapping; actual board address decoding is not inspected.

`0000: C3 2B 00` is `JMP 002B`. At `002B`, startup initializes I/O ports;
the jump at `0045` visits a small routine at `1DF8` which returns to `0048`.
Additional strong ordering evidence is code crossing every chip boundary:

- `07FD: MOV A,B; ANI 0F` feeds `0800: STA 8072`.
- `0FFE: CPI 07` feeds `1000: JZ 1024` in a comparison/dispatch chain.
- `17FE: 32 77 80` is a single `STA 8077` instruction split between chips
  43 and 44. The next instruction is `LDA 8005` at `1801`.

Startup at `00C5–00E9` sums ROM bytes in 2 KiB blocks and adds stored
checksums at `1FFC–1FFF`. The first three blocks use their full 2048 bytes;
the last stops before `1FFF`, including the preceding three checksum bytes.
Each result must be zero modulo 256:

| Label | Data sum | Stored checksum | Result |
|---|---|---|---|
| 41 | `12` | `EE` | `00` |
| 42 | `06` | `FA` | `00` |
| 43 | `82` | `7E` | `00` |
| 44 | `3B` | `C5` | `00` |

All pass. This is additional internal consistency evidence, not a trusted
external reference match; an 8-bit additive checksum cannot detect all damage.

Startup also contains write/read memory-test loops at `0120–016B`, using
the `8000` region and bit/address patterns. This and hardware-port setup are
consistent with standalone firmware, rather than a hosted application.

## Why the string scan misses the useful text

Individual images, all 24 concatenations, all 12 ordered two-chip byte-lane
pairs, and all 24 four-chip byte-lane permutations were revisited. ASCII,
high-bit-stripped ASCII, inverted-byte ASCII, CP866, KOI8-R, ISO-8859-5,
Windows-1251, and KOI-7-style shift-delimited candidates yielded no convincing
natural-language banner. Printable opcode fragments and FF padding account
for apparent hits. This does not rule out custom or packed text encodings.

The meaningful text is built from immediate constants in executable code:

- `0AC7` selects source `8011` and output buffer `81EE`.
- `0ACD` writes `N`, then `8072 + '0'`; `0AD8` writes `T`, followed by
  `8073 + '0'`.
- `0AE3–0AF5` emits a sign (`+` for a zero sign byte, `-` otherwise) and
  the first numeric digit.
- `0AF9–0B59` separates high/low nibbles, adds `30h`, and inserts decimal
  points at positions selected by `822B`.

The structural prefix is therefore `N<digit>T<digit><sign><numeric field>`;
the angle-bracket fields are descriptive placeholders, not literal ROM text.
Malformed internal values need not produce decimal digits: this is a formatter,
not proof of input validation or a recovered full protocol specification.

`0A62–0AC4` also constructs `P<value>`, `N<value>`, `M<value>`, or `XX`
and optional `Q`-prefixed status fields. `03h` serves as a local output-buffer
sentinel. At `188D`, the transmitter examines the *next* byte for this value
and changes a control output; do not assume it sends a literal ETX on the bus.

## Input commands and numeric processing

The parser starts with `HL = 8094` at `0BAD`, then processes bytes from
`8095`. It skips LF (`0Ah`), finishes at zero, and dispatches these letters:

| Letter / comparison | Observed effect (not a guessed command name) |
|---|---|
| `N` / `0BBE` | Stores the next low nibble at `8072`; for nonzero values parses a signed seven-digit field into `8051`, selects a record via `1C53`, and calls `1B03`. |
| `P` / `0BEE` | Stores the next low nibble at `8072`. |
| `T` / `0BFD` | Stores the next low nibble at `8073`. |
| `H` / `0C0C` | Parses a signed numeric field into `8225`, then invokes numeric/copy/storage helpers. |
| `R` / `0C45` | Sets flag `8257` to one; this affects status formatting. |
| `S` / `0C52` | Saves the next byte in `805C` and enters the handler at `1DD7` / `0E8D`, with a return path to the parser. |
| `U` / `0C66` | Consumes four low-nibble values for `8072`, `8073`, `8002`, `8074`, with corresponding validity/selection flags. |
| `V` / `0CC2` | Sets `8258`, saves the next byte in `8007`, and writes it to I/O port `A2`. |

The helper at `1D76` stores a separate sign byte (zero for `+`, one otherwise),
one digit byte, then three packed pairs of digits: five bytes representing a
sign and seven decimal digits. It masks nibbles without comprehensively
validating ASCII digits. The arithmetic at `1A38` branches on signs and uses
`ADC`/`DAA` and decimal-complement operations: strong evidence of signed BCD
addition/subtraction, not merely an incidental use of printable constants.

`1C53` selects 16-byte-spaced records in the `6000` region. The helper at
`1B03` writes five bytes from `8051`, changes port `60` around writes, and
reads back for comparison. This suggests controlled writable storage, but
does **not** establish EEPROM, battery-backed RAM, or any specific component.
Other indexing helpers use the `6100` and `6200` regions.

## Bidirectional bus interface: strongest identification clue

The formatted data is connected to real I/O code:

1. `1856–1861` copies 17 bytes from `81EE` into transmit buffer `81C2`.
2. `1883–188B` fetches buffered bytes and outputs them through port `F0`,
   with status polling at `F1` and control writes at `F2/F3`.
3. `18CF` establishes receive buffer `8095`; `18EE` reads `F0`, stores the
   byte, and adds a zero terminator. A counter initialized to `82h` bounds
   the receive loop. Completion sets flag `81DD`, used by the parser.
4. `183B` dispatches through a saved continuation pointer at `81D7`.
   Helper `1A26` can save a return address there and yield out of a polling
   loop. This is cooperative interface servicing, not just a single blocking
   string-print routine.

The command phase at `1979–19D3` separates bits `60h` from the low five
address bits, comparing the latter with the configured value at `8093`:

- Address class `20h` selects the receive/listen state (`81D9 = 1`).
- Class `40h` selects the transmit/talk state (`81D9 = 2`).
- `3Fh` clears the listen state; a different talk address clears talk state.

These precisely match the addressing conventions in NI's
[GPIB Messages reference](https://www.ni.com/en/support/documentation/supplemental/06/gpib-messages.html):
listen address = `20h + address`, talk address = `40h + address`, and
`3Fh` = Unlisten. Coupled with the actual receive/transmit state paths, this
is strong evidence of GPIB-style peripheral operation. It does not establish
electrical compliance, connector pinout, full IEEE-488 command support, or
SCPI. The instrument's letter commands are separate from these bus commands.

The `F0–F3` register group is also consistent with an 8255-style parallel
interface: `92h`/`82h` mode writes switch port A between input/output while
port B remains input; small control writes select individual port-C bits.
See the manufacturer's [82C55A datasheet](https://www.renesas.com/en/document/dst/82c55a-datasheet),
mode definition and bit set/reset sections. This identifies a programming
model, not a verified chip. It is not evidence of an ordinary UART link.

## Interpretation and next useful evidence

The best current hypothesis is a **programmable instrument or instrument
subsystem with an addressed GPIB-style interface and signed decimal data**.
Nothing yet establishes voltage, frequency, temperature, motion, or another
physical quantity. In particular, do not expand `T`, `V`, etc. into physical
units based on letters alone. A controller, measurement instrument, or
programmable source could all fit parts of this behavior.

A board photograph, CPU/peripheral markings, instrument front-panel labels,
or a manual containing this exact command grammar would be the highest-value
next evidence. Locally, isolated parser/formatter emulation and tracing the
sources of the numeric buffer at `8011` could narrow the function further.

## Reproduction and checks

From the repository root:

```sh
python3 unknown/k573rf5-set-41-44/analyze_code.py
python3 unknown/k573rf5-set-41-44/analyze_code.py --disassemble
```

The first command uses only Python's standard library and checks the manifest
hashes, combined order/hash, key opcode signatures, command comparisons, and
all four internal checksums. These are regression checks on static evidence,
not CPU execution tests. The second additionally requires Linux and `z80dasm`;
it disassembles selected ranges from seekable in-memory files, leaving the
repository unchanged. The disassembler uses Z80 mnemonic spelling for the
shared 8080 instruction subset; that is **not** a Z80 CPU identification.
Data, padding, and arbitrary entry alignment must not be interpreted as code.
