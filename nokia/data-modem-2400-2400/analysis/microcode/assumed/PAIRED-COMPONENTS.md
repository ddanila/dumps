# Two nonzero components reach paired arithmetic from reset

Under q3, handler 5 accepts an independently supplied byte U and a captured
16-bit word V. They reach the paired-arithmetic table as two nonzero components,
produce checked arithmetic outputs, and survive in R8–R11 through the terminal
continuation. This removes the zero-first-pair restriction of the earlier
[q2 capture experiment](PAIRED-CAPTURE.md). It still does not establish
independent operands within each add/subtract pair or identify physical DSP
input/output channels.

## The surviving input is at 317

All runs start with zero RAM/Q at 000. Inputs A5 at 002 and 60 at 076 give
Q=5, which selects handler 345 through Q-based dispatch at 109. Previous ALU
flags and early `[1,0]` replies at 117/106 remain unchanged.

| Read site | Diagnostic input | Result under q3 |
| --- | --- | --- |
| 317 | `(U-5)&FF` | R4 becomes U through D+Q |
| 118 | `(low(V)+1)&FF` | R6 becomes low(V) |
| 107 | `(high(V)+1)&FF` | R7 becomes high(V) |
| 38E | Entry 0–3 | Its Y value selects the entry at 38F |
| 36D | 0 | Releases the later carry-controlled continuation |
| Other sites | 1 | Retains the diagnostic default |

The handler calls 314–318 before calling 389. Under q3, 314/316 write D+Q to
R13, and 315/317 write D+Q to R4. R4 from 115 and 315 is overwritten before the
arithmetic call; the read at 317 controls the surviving first component.
Two controls change the earlier reads at both 115 and 315 to 00 or FF while
holding 317 fixed. Their entire trace suffixes from 318 onward remain equal.
This prevents attributing the final operand to an earlier transient load.

The same inputs under q1 give R4=0: 317 selects R10 rather than D+Q, and R10
is still zero at that point. The read log explicitly distinguishes sampled D
from D selected by the ALU. These matched controls expose a source-field
ambiguity rather than validating q3 as the physical decode.

## Arithmetic and the exit condition

At the 38F call, q3 has R4–R11 equal to
`[U, 0, low(V), high(V), U, 0, low(V), high(V)]`, with Q=5. The wrapper copied
the source registers; the operands within each pair are equal. The four table
entries expose the following two 16-bit results, low byte first:

| Entry | First result | Second result |
| --- | --- | --- |
| 0 | 2U | 2V modulo 65536 |
| 1 | 0 | 2V modulo 65536 |
| 2 | 0 | 0 |
| 3 | 2U | 0 |

The verifier compares all four ALU/Y bytes, including carry propagation, with
independent whole-word arithmetic. Table instructions preserve RAM and Q.
The previous-zero branch at 390 tests **only the second result's high byte**.
It does not combine the first and second results into a zero test.

For example, reset inputs U=FF and V=0001, entry 0, produce
**FE 01 02 00**: first result 01FE, second result 0002. The branch returns and
the run reaches 084 at cycle 110 even though both results are nonzero and the
first high byte is 01. With V=0080, entry 0 produces a final high byte of 01
and repeats every 12 instructions. Entry 3 returns even with first result
01FE because its second result is zero.

R4 is overwritten in the continuation, but R8/R9 preserve U/00 and R10/R11
preserve V. This is an actual reset-to-terminal data path under the assumptions,
not a local fixture with initialized registers or injected returns. The four
output bytes remain transient ALU/Y results with the existing virtual capture
rules; no new physical write-enable claim is introduced.

## Scope and verification

[Configuration](paired-components-study.json), [runner](paired_components_study.py)
and [report](results/paired-components-study/report.json) retain the diagnostic
assumptions, source hashes, every run and 16 complete witness traces.

The q3 sweep uses every U byte, V in 0001/0080/8001/FFFF, and all four entries:
4,096 runs, of which 3,072 reach 084 and 1,024 repeat. The matched q1 controls
use U=00/FF with the same V/entry combinations: 32 runs, with 24 terminal and
8 repeating. Two additional q3 runs verify the overwrite controls. All 4,130
runs execute 160 instructions cleanly, without unused words or stack faults.
Exact-state recurrence uses the timing study's registers/flags/stack/input-phase
key; repeating outcomes are not inferred from the final PC alone.

This is a complete U-byte sweep across four V slices, not an exhaustive sweep
of the 24-bit U/V input space. The 91-test suite includes the nonzero-first-high
counterexample and rejects a corrupted arithmetic output. The saved full
witnesses replay byte for byte. Annotation coverage remains 362 distinct words;
existing routines gain stronger reset-path interpretations.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/paired_components_study.py --out /tmp/nokia-paired-components
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -p 'test_*.py'
```
