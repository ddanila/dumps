# The q3 paired self-arithmetic wait at 370

370–378 copies R0 to R1, preserves two 16-bit input words and Q, calls one of
four arithmetic entries, and repeats according to the final high byte exposed
by that entry. The table arithmetic changes no RAM. With unchanged inputs and
a fixed entry, a failed first test therefore cannot make progress on later
passes.

The contract uses q3, previous-zero loop control and the existing four-entry
table at 379–388. All runs start at the actual BSR at 309 with an empty stack;
real PLP, computed BSR, POP, BLT and final POP instructions manage the frames.
These local fixtures do not establish that a particular reset scenario reaches
309 or identify a physical consumer of the transient output.

## Four entry results

Define `U=R4+256*R5` and `V=R6+256*R7`, with the low byte first. Each table row
exposes four consecutive Y bytes, low/high for each of these two results:

| Index | Entry | First word | Second word |
| --- | --- | --- | --- |
| 0 | 379 | 2U modulo 65536 | 2V modulo 65536 |
| 1 | 37D | 0 from U−U | 2V modulo 65536 |
| 2 | 381 | 0 from U−U | 0 from V−V |
| 3 | 385 | 2U modulo 65536 | 0 from V−V |

The low-byte add/subtract supplies carry to the following high-byte operation.
There is no independent second operand in these q3 rows: their A and B fields
select the same register. All table destinations are no-load. In the wrapper,
371–374 copy R4–R7 to themselves; 370 copies R0 to R1. R0, R2–R15 and Q remain
unchanged throughout a complete call.

## Return and recurrence

377 performs its own transient `R0 AND Q`, but under previous-flag timing the
BLT tests the **preceding table instruction's zero flag**. It repeats when the
second result's high byte is nonzero. 378 exposes zero and returns otherwise.

Entries 2 and 3 always return after one pass. Entries 0 and 1 return exactly
when `((2*V)>>8)&255 == 0`, which means either:

- V is between 0000 and 007F inclusive; or
- V is between 8000 and 807F inclusive.

There are 256 such V values out of 65,536. A nonzero low byte does not prevent
return: V=8001 produces the word 0002 and returns. The first result's high
byte also does not control the loop.

A returning call executes 14 instructions including the caller. A repeating
pass takes 12 instructions: seven wrapper instructions, four table
instructions and the BLT. Since the operands and Q do not change, repeated
headers have identical RAM/Q, previous ALU flags/Y, carry feedback, PC, stack
pointer, depth and stack slots. Each read is held constant and each dispatch
selection is fixed, so neither can change a later outcome. The checker records
two complete passes and proves period 12 from the equal headers; it does not
infer persistence from a timeout.

Maximum stack depth is three: caller, loop and table call. Successful return
reaches 30A with depth zero. A repeating header at 370 retains just the caller
frame, with depth one. No frame is injected or repaired.

## Input at 375 as a dispatch candidate

375 exposes its external D byte directly on Y. 376, the computed-call
instruction, instead exposes zero. This gives a concrete distinction between
possible index sources:

- With preceding-Y indexing, the table entry is `D375 modulo 4`.
- With current-Y indexing, every D375 byte selects entry zero.

The study checks all 256 D375 values through the ordinary executor under the
preceding-Y hypothesis. On a fixed fixture with V=1234, inputs selecting entries
0/1 repeat, while entries 2/3 return. A test compares preceding and current Y
using the same D375=3, demonstrating targets 385 and 379 respectively.

This identifies a useful software dispatch hypothesis, not a recovered input
port or controller command. The input is supplied explicitly by the scenario.
It does not change U or V, and no autonomous sample progression is inferred.

## Evidence

The exhaustive study runs every V byte pair under all four table entries:
262,144 local calls. U is V XOR A55A in that plane, so it also spans every
16-bit value but is correlated with V. Q follows the declared fixture. Complete
retained RAM/Q, every helper PC and Y, instruction count, outcome and period
are checked against independently written formulas.

| Entry | Returns | Period-12 repeats |
| --- | ---: | ---: |
| 0 | 256 | 65,280 |
| 1 | 256 | 65,280 |
| 2 | 65,536 | 0 |
| 3 | 65,536 | 0 |

Twenty-eight saved boundary witnesses compare every local trace field with the
ordinary executor. Sixty-four independently randomized RAM/Q/input tests break
the U/V fixture correlation and cover fixed and preceding-Y dispatch. The
256 ordinary-executor input controls preserve per-case digests and four full
boundary witnesses, bringing the saved local witness total to 32.

[Configuration](pair-wait-study.json), [runner](pair_wait_study.py), and
[report and witnesses](results/pair-wait-study/report.json).

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/pair_wait_study.py
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -p 'test_*.py'
```
