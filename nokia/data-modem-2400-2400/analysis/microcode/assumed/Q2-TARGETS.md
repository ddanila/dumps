# q2 can capture a nonzero R10, but the tested polls still use reset zero

*Runs under the [shared assumptions](ASSUMPTIONS.md).*

The [reset caller study](Q2-CALLER.md) reached the masked polls with R10=0.
The wider [target study](q2_target_study.py) checks all eight global dispatch
indices and all 256 default external bytes, with diagnostic zero replies at
117 and 106. It finds a reset-reachable source of nonzero R10, but no tested
path delivers that written value to either masked helper.

This remains the retained q2 mapping combined with the separately hypothesized
previous-flag/defined-carry policy. Dispatch indices are scenario inputs,
not recovered hardware signals. A global index also selects entries at nested
calls; this is not an exhaustive search of independently chosen table entries.

## The complete writer set

Exactly six used instructions write R10 under q2:

| PC | Effect on R10 |
| --- | --- |
| 094 | Copy R0 |
| 38C | Copy R6 |
| 3DC | Copy R12 |
| 3E0 | Copy R10 to itself |
| 3E4 | Negate R12 modulo 256 |
| 3E8 | Negate R10 modulo 256 |

The decoder checks this set over the complete store, including writers that
leave the register unchanged. Only 38C executes in the tested reset runs.
This does not rule out the other writers under different inputs or dispatches.

## Where the nonzero value comes from

Global dispatch index 5 selects 109 → 10F → 345, which calls 314 and then
389. At 38A–38D, the code copies R4–R7 into R8–R11. In particular, 38C copies
R6 into R10. Its source's last writer is 118, the second instruction of the
early input wait, and its value is `(D−1) mod 256`.

The input stream at 117 supplies D and then zero. Under previous-flag timing,
the zero addition permits the following 118 to leave the wait. However, 118
still reads the default D and overwrites R6 with FF+D modulo 256. The analogous
106/107 pair supplies the same value to R7. Thus a zero reply does not imply
that the captured register is zero. D=00 produces R10=FF; D=01 produces zero;
D=55 produces R10=54. These values arise through ordinary ROM execution,
without injecting a target register or jumping into a helper.

The wrapper calls the paired-arithmetic table at 38F. Global index 5 selects
396–399. This entry computes a difference for the first copied pair and a sum
for the second, without storing those ALU results in RAM. The loop at 390
uses the preceding zero flag from 399. With R6=R7=R10=R11=v, that last result
is `(2*v + carry(2*v)) mod 256`. It is zero only for v=0. D=01 therefore
returns; the other 255 values repeat a 12-instruction cycle. No masked helper
is visited on this path, including the returning case.

## Scope and evidence

All **2,048 executions** are clean and reach a repeated complete modeled
state within 512 cycles. Repetition keys include RAM, Q, previous ALU results,
the full stack state, next PC, and each input stream's remaining suffix.
They establish actual cycles under these stubs rather than timeout guesses.

| Global index | Return to terminal 084 | Other inputs |
| --- | --- | --- |
| 0 | D=00 | 255 repeat the first masked poll |
| 1, 3, 6, 7 | All 256 bytes for each index | None |
| 2 | D=02 | 255 repeat the 1EC/1ED wait |
| 4 | D=01 | 255 repeat the paired-arithmetic loop at 3A2 |
| 5 | D=01 | 255 repeat the paired-arithmetic loop at 389 |

Only index zero visits 126 or 12C. At each visited helper entry, R10 and Q are
zero and R10 has no earlier writer. Index 5 is the only choice that writes
R10. The two sets of paths are disjoint in this experiment. Consequently,
nonzero data provenance is now partly identified, but a nonzero poll target
from a continuous reset execution remains unestablished. Physical restart,
external data source, dispatch wiring and the useful modem operation remain
open; no default mapping or scenario changes.

The [configuration](q2-target-study.json) fixes the assumptions. The
[report](results/q2-target-study/report.json) records every run's first target
writes, source writers, helper entries, repeat periods and trace hashes.
Sixteen full witnesses cover every index with D=00 and D=55.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/q2_target_study.py
```
