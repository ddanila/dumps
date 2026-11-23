# Preceding Y selects nontrivial q2 paired-arithmetic paths

At call 38F, q2's preceding ALU result is a plausible dispatch index: it
carries the external byte read at 38E. Using it lets nonzero captured values
return from the 389 wrapper. Current Y and Q instead select a single entry.
This narrows a useful dispatch hypothesis without identifying physical wiring.

The [target provenance study](Q2-TARGETS.md) used one constant index for every
dispatch, including 109 and 38F. Its index-5 path copied captured data into
R10, but almost always repeated the paired-arithmetic loop. The new
[study](q2_dispatch_study.py) holds every other assumption fixed and changes
only the index source at 38F. It compares scenario index 5, current Y, Q and
preceding Y over all 256 default input bytes.

## An index prepared immediately before the call

Under q2, 38E computes `D−R14 mod 256`, without writing RAM. In these reset
traces R14=0, so its Y is D. The following 38F computes zero AND Q, making its
own Y zero; Q also remains reset zero. Therefore:

| Candidate source at 38F | Index in these reset runs |
| --- | --- |
| Scenario | 5, reduced to entry 1 |
| Current Y | 0 |
| Q | 0 |
| Preceding Y | D, reduced modulo 4 |

The four hypothesized table entries are the existing POP-delimited paths:

| Entry | Addresses | First pair | Second pair |
| --- | --- | --- | --- |
| 0 | 392–395 | Add | Add |
| 1 | 396–399 | Subtract | Add |
| 2 | 39A–39D | Subtract | Subtract |
| 3 | 39E–3A1 | Add | Subtract |

Each pair is a low/high-byte operation, with carry linked into the high byte.
These instructions expose ALU results but do not store them into RAM. Their
physical output consumer remains unidentified. The first pair uses R4/R5 and
R8/R9; the second uses R6/R7 and R10/R11. The wrapper has just copied each
source pair into its corresponding second operand.

Under the shared previous-flag policy, BLT at 390 tests the final high-byte
result of the selected table entry. Subtracting a copied pair gives zero, so
entries 2 and 3 release the wrapper. Entries 0 and 1 end in addition. In these
reset traces R6=R7=R10=R11=v, where `v=(D−1) mod 256`, and the last sum is
`(2*v + carry(2*v)) mod 256`. It is zero only for D=1. This is a high-byte
condition, not a general test that an entire 16-bit result is zero.

## Where the released values go

For preceding-Y indexing, the wrapper returns for D=1 and for every D whose
low two bits are 2 or 3: **129 of 256 inputs**. It returns normally from 391
to 347 with R10 still equal to the captured `D−1` value. No register result,
program-counter jump or synthetic return is injected.

The continuation reaches the carry-controlled loop at 36C–36E. Its first
36C sees R0=FF and adds D; 36D then adds D and the preceding carry. For these
nonzero D values, the result at 36D is `2*D mod 256` and its carry is set
exactly when D is at least 128. Previous-carry loop control therefore divides
the released cases into 65 terminal runs and 64 three-instruction cycles.
The nonzero values have passed the first arithmetic wrapper; they have not
established a complete streaming workload.

| Index source at 38F | Terminal 084 | Paired loop, period 12 | Carry loop, period 3 |
| --- | --- | --- | --- |
| Scenario 5 | 1 | 255 | 0 |
| Current Y | 1 | 255 | 0 |
| Q | 1 | 255 | 0 |
| Preceding Y | 65 | 127 | 64 |

All **1,024 runs** are clean. Each outcome has a repeated complete modeled
state within 512 cycles, including input-stream suffixes, RAM, Q, ALU flags
and stack contents. At completion R10 remains `D−1` in every run. None visits
the masked helpers at 126 or 12C. The earlier failure to deliver a nonzero
poll target thus persists even when this arithmetic loop can return.

## Interpretation and reproducibility

Instruction placement and the data dependency support testing preceding Y as
an index source. More coverage or more terminating cases cannot prove it is
the board's wiring. The top-level index remains a scenario-supplied 5, the
early zero replies remain diagnostic input streams, and the previous-flag
policy is still a separate hypothesis. No default mapping or scenario changes.

The [configuration](q2-dispatch-study.json) records these choices. The
[report](results/q2-dispatch-study/report.json) contains all runs, initial
index operands, return events, carry-loop calculations, complete final states,
repeat periods and source/trace hashes. Twenty-four complete witnesses cover
D=00,01,02,03,82,FF under each source.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/q2_dispatch_study.py
```
