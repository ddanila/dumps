# q2 handler 133 gates transforms on accumulator carry

*Runs under the [shared assumptions](ASSUMPTIONS.md).*

Under the retained q2 mapping and previous-flag policy, the prefix of handler
133 adds an external byte to Q. It bypasses three transform calls when that
addition does not carry. On carry, a comparison of the **old** Q against R7
selects either the last call or the beginning of the three-call sequence.
This gives a local interpretation of previously unannotated control flow;
it does not establish a physical phase accumulator or modulation algorithm.

## Exact prefix behavior

Let q be Q on entry to 133 and d the external byte consumed at 138. After
the prefix, the registers are:

| Destination | Result |
| --- | --- |
| Q | `(q+d) mod 256` |
| R0, R5 | q |
| R2 | Old R3 |
| R3 | `255−old R1` |
| Other RAM registers | Unchanged |

Call 133 enters 341–344. Under q2 these four instructions each copy Q into
R0, establishing a snapshot of the old accumulator. This apparently redundant
sequence is a property of this candidate decode, not evidence that the board
really performs four identical writes. Other retained mappings give this
preparation different register/operand roles.

134 copies the snapshot into R5. 136 preserves old R3 in R2, and 137
complements R1 into R3. That complement always clears carry, so 138 adds D to
Q without an incoming carry. The remaining branch decisions are:

| Condition | Next PC | Meaning of the following code |
| --- | --- | --- |
| `q+d < 256` | 13E | Skip all three transform calls |
| `q+d >= 256` and `q < R7` | 13D | Enter the call to 3C0 |
| `q+d >= 256` and `q >= R7` | 13B | Enter calls to 3EA, then 3D5, then 3C0 if each returns |

139 computes `R0−R7`, but its branch consumes the preceding addition's carry.
If the addition carried, execution reaches 13A, whose branch consumes the
comparison carry from 139. Equality therefore selects 13B, and an addition
exactly equal to 256 takes the carry path. The predicates use q, not the
updated Q. The local study stops at these three destinations: it does not
assume that the subsequent transform wrappers return for arbitrary fixtures.

## Local checks and reset reachability are separate

The [study](q2_accumulator_study.py) checks **132,608 local executions** against
an independent arithmetic prediction, comparing the entire RAM array, Q and
next PC:

- All 65,536 q/d combinations with R7=0 check the addition and carry gate.
- All 65,536 q/R7 combinations with D=FF check the threshold gate whenever
  carry is reachable; q=0 correctly bypasses it.
- All 256 R1 values at six addition boundaries check that the complement
  setup never injects carry into the addition.

These are exhaustive sweeps of the stated subspaces, not every possible
joint RAM/Q/input state. Nonzero Q is explicitly supplied to a local entry
at 133. The one nested ROM call at 133 returns through the real sequencer
stack. Fifteen complete integrated traces for representative cases are compared
instruction by instruction with the component probe, including ALU flags and
branch decisions.

A separate set of **256 reset runs** uses global dispatch index 7, all default
input bytes, and the previously documented zero replies at early waits.
Every run reaches 133 with Q still zero, updates Q to D, then branches from
139 to 13E without entering a transform wrapper. All reach terminal 084.
Thus successful reset execution of this handler has not exercised its
carry-triggered transform paths. A source of nonzero Q on a later invocation
or a physical restart retaining state remains unestablished.

This is consistent with an accumulator-controlled operation under q2, but
calling it carrier recovery, symbol timing, or a waveform generator would
require evidence linking the accumulator, input source, and transform outputs
to the hardware. The default mapping and scenarios remain unchanged.

## Reproduce

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/q2_accumulator_study.py
```

The [configuration](q2-accumulator-study.json) records the mapping, condition
policy and fixtures. The [report](results/q2-accumulator-study/report.json)
contains category counts, a digest of all local comparisons, full local
witnesses, reset gate events, final states, and source/trace hashes. Four
complete reset traces cover D=00,01,80,FF.
