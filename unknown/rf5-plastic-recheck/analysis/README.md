# RF5 content survey, 2026-09-20

## Conclusion

The two matching 2048-byte reads contain nontrivial, nonblank, repeatable data,
but this survey has not identified executable firmware or a CPU family.
Priorities were architectures usable in USSR systems: 8080/Z80, MCS-48,
MCS-51, and PDP-11-compatible machines. The last family is 16-bit; a single
8-bit ROM could be only one byte lane of its program. Board origin and any
companion ROM would materially help resolve that possibility.

Repeatability is not proof of correct address order, pin routing, or intact
stored contents. Do not erase this chip on the basis of the inconclusive CPU
identification. No hardware operation was performed for this survey.

## Strings

All raw ASCII runs of at least four printable characters are:

| Offset | Text |
|---|---|
| `0058` | `..wM` |
| `00F5` | `&bU%` |
| `0257` | `d&3&` |
| `02FC` | `NLk%&` |

None resembles a message, version, product name or command. No ASCII run is
six characters long. UTF-16 ASCII searches in either endian order and either
alignment found no runs of four characters.

KOI8-R, CP866 and CP1251 Cyrillic-letter runs were examined. Examples such as
KOI8-R `ШКОШШЭЭШ` and CP866 `ХХЧЭдэс` do not supply recognizable Russian text.
Simple inversion, per-byte bit reversal, their combination, high-bit toggle,
and high-bit stripping also yielded no convincing text. These are limited
transformation checks, not an exhaustive search of encodings or wiring faults.
All extracted runs, including incidental transformed matches, are in results.json.

## Byte structure

- SHA-256: `0d693747f3352268797ff32114173820724a2761607609aa656cfb1d0a2c45a9`.
- 221 distinct byte values; empirical byte entropy about 6.9065 bits/byte.
- Most frequent bytes: `F1` (85), `BC` (75), `D1` (54), `06` (51), `26` (50).
- Every data bit takes both values; the two 1 KiB halves differ.
- Repeated local sequences occur, especially around offsets `0300..06FF`.
  This is structured data, not a uniform blank or the earlier output echo.
- A visual 8-by-8, byte-per-row glyph survey did not resemble a conventional
  contiguous font. Other character layouts and graphics formats remain possible.

Entropy and opcode frequencies cannot distinguish code, tables, microcode,
encoded material or reproducibly misread contents on their own.

## Disassembly checks

Listings use MAME unidasm 0.285, linear sweeps from file offset zero. Addresses
are provisional file offsets, not a recovered memory map. No entry point or
code/data boundary has been established, so decoding data will produce false
instructions. Operand bytes may also contain apparent opcodes.

| Family | Observation | Assessment |
|---|---|---|
| 8080 / Z80 | Many compare/ALU operations and pops; the Z80 sweep has 111 POP versus 5 PUSH instructions. Raw C3/CD candidates point throughout the 64 KiB address space. | No coherent program identified; the stack imbalance is suspicious, not a proof of invalidity. |
| MCS-48 / 8035 | 125 illegal lines among 1525 decoded lines, mixed with frequent port and flag operations. | Weak as a straight program image. Embedded data or another mapping can still explain illegal regions. |
| MCS-51 / 8051 | Many valid instructions, but no convincing initialization or routine structure identified. | Inconclusive: almost every byte decodes, so validity alone says little. |
| PDP-11 compatible | Direct adjacent-byte pairing gives 119 `.WORD` lines among 702 lines and no convincing entry sequence. | No direct identification. A single byte lane cannot be reconstructed without its mate. |
| 6502 / 6800 / 6809 | Secondary comparison listings saved; no convincing program recognized. | Lower-priority alternatives, not positively identified. |

The `i8085.asm` file is explicitly an **8085** disassembly, used as a shared
8080-family mnemonic view; it is not an exact 8080 validator. The decoder
accepts 8085-only/undocumented instructions, so its zero illegal count cannot
establish 8080 compatibility. The local MAME source itself notes that an
8080-specific mode is absent. Z80 likewise decodes many arbitrary byte streams.

A raw search finds 28 occurrences of C3/CD with two following bytes. Only six
candidate targets fit the best aligned 2 KiB window, `F000..F7FF`. This does
not identify a load address: some matches are operands/data, and real code can
call other ROMs. In particular, this chip need not hold a reset/boot entry.

No encryption, compression, microcode format, or byte-lane interpretation has
been demonstrated. Those remain alternatives, not identifications. A useful
next offline step would require board/chip provenance, a companion dump, or a
known image from the same equipment. Additional reads alone cannot identify
the architecture now that repeatability is established.

## Reproduce

Run `python3 analyze.py /path/to/unidasm` from any directory. It reads the
parent `read1.bin`, regenerates `results.json` and the eight `.asm` files.
Without the optional executable argument, it regenerates only byte/string
statistics. unidasm came from the Ubuntu `mame-tools` package version
`0.285+dfsg1-1`, extracted outside the repository without system installation.
