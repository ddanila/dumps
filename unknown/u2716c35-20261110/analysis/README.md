# U2716C35 functional analysis — 2026-11-10

**High confidence: a Z80 firmware component containing keyboard matrix scanning,
key translation, held-key/repeat handling, and a 64-byte event queue.** It is
linked at **6800h–6FFFh** and depends on substantial firmware elsewhere. It is
not a complete standalone PC1715 keyboard image. The exact machine, manufacturer,
language layout and firmware revision remain unknown.

Analysis uses only the preserved `../rom.bin`, SHA-256
`b97cfb4b68b56690c27730daaa347a8780579c8aa75d0169979cc63e33044b34`.
No programmer, serial connection, physical chip, or RF2 experiment was accessed.

## Address map and evidence for the origin

The 6800h origin is inferred from mutually consistent absolute code and data
references, then exercised by running original code in libz80ex. For example:

- Offset 0225h calls 6AE4h; offset 02E4h is precisely the matrix scan routine.
- Offset 03F3h calls 6CD8h; offset 04D8h is the key emission routine.
- The translator references 6D5Dh and 6D7Dh, matching embedded tables at
  offsets 055Dh and 057Dh.
- Calls to 686Ah land on a real jump-table entry (`JP 0637h`).

The first bytes should therefore be interpreted as header/table data, not as a
reset routine merely because the file starts with an `LD SP` opcode value.

| ROM offset | CPU address | Interpretation |
|---|---|---|
| 0000–0037 | 6800–6837 | Word-oriented header, apparently pointers; exact roles unknown |
| 0038–0057 | 6838–6857 | FF padding |
| 0058–01C5 | 6858–69C5 | 122 consecutive three-byte `JP` entries |
| 01C6–01DD | 69C6–69DD | FF padding |
| 01DE–055C | 69DE–6D5C | Keyboard routines and interrupt entry points |
| 055D–0580 | 6D5D–6D80 | Translation data |
| 0581–05F8 | 6D81–6DF8 | Wrappers/patch-like routines calling other ROMs |
| 05F9–07FD | 6DF9–6FFD | 517 bytes of FF padding |
| 07FE–07FF | 6FFE–6FFF | `F6 3D`; unidentified trailer, not a verified checksum |

Of the 122 dispatch entries, 105 point below 6800h, four point into this chip,
and 13 contain `JP FFFFh`. Those last entries appear reserved/unimplemented;
without the rest of the memory map, their exact use is unknown. This looks like
a shared firmware dispatch table, not 122 independently recovered functions.

## What the code does

### Scan a 12 × 8 active-low matrix

`6AE4h` preserves the high nibble of port C8h and cycles its low nibble through
0–11. For each selection it reads eight active-low inputs from C9h. It finishes
by writing selector 15. Each pressed position is stored as
`2 * (row * 8 + bit)`, suitable for indexing a two-byte-per-key table.

The current snapshot at 789Fh contains up to three positions, three states at
78A2h, and a count at 78A5h. The previous snapshot is at 78A7h. A newly seen key
receives state 1; a key previously in state 1 advances to 2; other prior states
are retained. A fourth detected key sets count 4 and aborts scanning before
storing a fourth position. The caller explicitly handles this sentinel.

This is executable evidence of a keyboard-like matrix, not merely a visual
guess based on apparent Z80 opcodes. Physical row/column orientation is unknown.

### Translate and process keys

`6B4Bh` translates a position through a table at **7130h**, outside this dump.
Flags select one of the two bytes per position. It then invokes a callback using
a pushed return-address chain. Callers distinguish special/control codes,
including A5h, ABh, BDh, and E2h–EAh, and update persistent flags.

`6C42h` and `6C76h` implement additional translations; `6C8Fh` consults a further
external sequence table at **71F0h**. `6D0Bh` contains a held-key countdown and
re-emission path. The actual key legends, alphabet, modifier names and produced
text cannot be recovered reliably without these external tables and callers.

Port B2h receives control-like bytes 43h/C7h and counts 14h/28h in the special-key
path. A timer is plausible, but the peripheral and its physical purpose are not
identified. Do not interpret these writes as a confirmed serial host protocol.

### Queue events

`6CE7h` stores a byte through the write pointer at 78B3h, advances it and wraps
from 7982h to **7942h**: a 64-byte circular buffer at **7942h–7981h**.
It checks for collision with the read pointer at 78B5h and sets overflow flags.

The normal dequeue path in `6D0Bh` reads through 78B5h, copies the byte to 78B2h,
advances/wraps the pointer, and sets bit 0 at 78B1h to indicate availability.
The empty-buffer paths also handle repeat and special conditions. General
key emission calls through 686Ah into missing firmware at 0637h; we cannot
reconstruct the entire event path from this chip alone.

`69E1h` and `6A1Fh` are interrupt-shaped routines ending in `RETI`. Their
`RST 10h` / `RST 18h` dependencies are also outside the chip.

## Execution checks and reproducibility

`probe.py` executes original bytes using the installed libz80ex CPU emulator.
It supplies synthetic RAM, a stack and an inferred matrix-port model. It does
not replace missing firmware with dummy successful returns, and rejects execution
outside the available routine region. This is isolated function execution, not
a boot of the unidentified machine or proof of its electrical interface.

Passing checks in `probe-results.json`:

- Every one of the 96 positions yields the expected doubled matrix index.
- Each position transitions from new to held and disappears from the count on release.
- Zero, two, three and four simultaneous keys behave as described above.
- Enqueue/dequeue preserves the test byte and advances both pointers.
- Both queue paths wrap correctly at the end of the 64-byte buffer.

`blocks.txt` distinguishes code from data and padding; `symbols.txt` assigns
analyst-selected functional names. `disassembly.asm` reassembles byte-for-byte
to the original dump with z80asm. The disassembler's self-modifying-code warning
is a heuristic warning, not a finding that this EPROM is modified at runtime.

From this directory:

```sh
python3 probe.py
z80dasm -a -t -l -g 0x6800 -b blocks.txt -S symbols.txt -o disassembly.asm ../rom.bin
z80asm -o /tmp/u2716-reassembled.bin disassembly.asm
cmp ../rom.bin /tmp/u2716-reassembled.bin
python3 compare_fragments.py /tmp/u2716-referencecheck /tmp/u2716-s6130
```

## Identification search and limits

The acquisition record already documents no exact match in 134 distinct
reference images. This follow-up also searched for **any identical 16-byte
window containing at least six distinct byte values**, to find related code
even if relocated or embedded in a different image. No such window matched
in 269 reference entries (247 unique byte contents) from the cached collection
and the additional S6130/Elema repository. Archive members and combined/split
images are counted separately; this is not 247 different machines. Sources and
hashes are recorded in `fragment-comparison.json` and the parent comparison record.
This criterion can miss related code with frequent changed addresses.

The possible Robotron provenance remains an owner-supplied lead. A typewriter,
terminal, or other larger keyboard-equipped system is plausible. A 12 × 8
matrix alone is not sufficient to select a model. For example, the original
[Hübner keyboard-controller documentation](https://www.sax.de/~zander/zx/spectral/spc_tast.pdf)
describes K7659/S6001–S6030 keyboards, but it does not establish that our firmware
belongs to those machines.

The [S6130 restoration's firmware and hardware analysis](https://github.com/radiolok/robotron_s6130)
provides a useful comparison: its ordinary ROM map is 0000h–37FFh, working RAM
is 4000h–5FFFh, and its keyboard ports differ. It is not a match to this image.
The archived [T6010.ASM](https://www.tiffe.de/robotron/Archiv-Sebastian-Simon/CPM/ASM/S6010/T6010.ASM)
is a small host-side keyboard driver using ports 0Dh/0Fh, not the missing firmware.

The most useful additional evidence would be a photograph of the original board
or chip label, adjacent ROMs (especially the one covering **7000h–77FFh**), or a
candidate firmware set with keyboard ports C8h/C9h and work RAM around 7800h.
Until then, preserve the image under `unknown/` and identify its **function**, not
an unsupported product name.
