# The ROM/carry wait has a finite feedback recurrence

The [handler comparison](ROM-GATE-HANDLERS.md) showed that the two-bit ROM-read
gate creates a wait at 36C–36E and that a zero reply releases it. Exhausting all
constant reply bytes shows a richer behavior: **215 bytes eventually return;
41 enter persistent cycles** under this hypothesis. It is therefore not
justified to name this mechanism a zero-acknowledgement protocol.

## Derivation

Retain q3, previous-carry loop control, R0=FF, default D=1 except at 36D, and
the raw-bit ROM gate `11.4=0 AND 18.5=0`. Let d be the constant external reply
at 36D, x the preceding Y byte used to address the next ROM read, and
`T[x] = ROM[256+x]`. The three instructions give:

1. 36C adds T[x] to FF, writes `R1=(T[x]-1) mod 256`, and sets carry iff T[x]
   is nonzero. Its Y output is the old R0, FF.
2. 36D adds d and that carry to R1. Define `s=255+d` when T[x]=0, otherwise
   `s=T[x]+d`. It writes `R2=s mod 256` and sets carry iff s is at least 256.
   Its Y output is R1, not R2.
3. 36E adds default D=1 to R2 without carry feedback, writes `R3=(s+1) mod 256`,
   and exposes R2 on Y. BLT tests the previous carry from 36D.

Thus the iteration returns when s<256; otherwise it repeats with
`x = s mod 256`. R0 and Q are preserved. The next ROM address follows the
**A-register Y output**, not the last ALU arithmetic result. Replacing that
Y behavior changes the recurrence and is rejected by the tests.

The reset path enters at cycle 84 with initial address byte x=0. The local
transition checker also covers all other x values, but those are hypothetical
entry states rather than additional demonstrated reset entries.

## Exhaustive results

Every one of the 256×256 address/reply transitions is compared against three
actual Am2901 steps with the decoded fields and carry-feedback policy. Every
starting pair is then classified by walking the finite graph until either
return or a repeated address. Of those 65,536 entry pairs, 62,170 eventually
return and 3,366 repeat. This graph proof follows from checked individual
transitions; no timeout is used to classify it.

All 256 reply bytes are also run from actual zero reset in the integrated
emulator, with the same two-bit gate across the whole control store. Each run
executes 512 instructions cleanly, with no unused words or stack faults. The
observed ROM addresses, all three ALU results, Y output and loop test match
the predicted trajectory. Complete-state recurrence independently confirms
the predicted cycle periods in the repeating cases.

| Reply (hex) | Behavior from reset | Consequence |
| --- | --- | --- |
| 00 | Return after one iteration | First 084 at cycle 110 |
| 01 | Fixed address x=0 | Three-instruction cycle |
| 02 | Return after two iterations | First 084 at cycle 113 |
| 77 | Transient followed by a fixed address | Three-instruction cycle |
| F9 | Cycle of 15 address states | 45-instruction cycle |
| FB | Return after 13 iterations | First 084 at cycle 146 |
| FF | Cycle of 11 address states | 33-instruction cycle |

Among the 215 returning replies, 190 return after two iterations. The maximum
is 13 iterations; among the 41 repeating replies, 25 have a one-address cycle.
For every returning reply, the first terminal cycle is
`110 + 3*(iterations-1)`. This includes the real continuation after the loop,
not an injected return or an assumed completion marker.

The longer cycles can address bytes outside the quarter-sine interval. The
upper bank contains other patterns as well as the sine quarter, and this
read-policy hypothesis exposes all 256 bank entries. Calling every lookup a
sine sample would therefore be incorrect.

## Interpretation and artifacts

This result characterizes an executable interaction between the ROM-read
hypothesis and a real microcode carry loop. It does not validate the predicate
as hardware wiring, establish a physical reply byte, or identify a DSP purpose
for the recurrence. In particular, reaching a terminal loop for more reply
values is not evidence that one gate is more correct.

[Configuration](rom-carry-replies.json), [runner](rom_carry_replies.py), and
[report](results/rom-carry-replies/report.json) retain all 256 reset trajectories,
the local-check counts, source hashes and seven full witnesses. The full study
reproduces byte for byte. The 96-test suite includes the longest returning and
repeating examples, intermediate transition checks and a negative Y-output
mutation. Existing defaults and the count of 362 annotated words are unchanged.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/rom_carry_replies.py --out /tmp/nokia-rom-carry-replies
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -p 'test_*.py'
```
