# The adjustment is transient in the current model

*Runs under the [shared assumptions](ASSUMPTIONS.md).*

The [conditional one-unit adjustment](FRAGMENTS.md) changes Y for one
microinstruction, but does not survive in modeled state after the paths join.
This limits the routine label: it describes an observed ALU operation, not a
demonstrated change to a stored sample or external output.

## State comparison

The fragment sweep now records state after each of the three tail words,
including RAM, Q, all ALU results/flags, carry feedback, PC, stack pointer and
physical stack contents. All 40,960 paired fixtures across the four candidate
layouts have:

1. Different first Y values, separated by one modulo 256.
2. Equal datapath state after the second instruction, including flags and
   carry feedback. PCs still differ because the paths occupy different words.
3. Equal complete recorded state after the final branch to 07B.

The decoding explains this convergence. The first operation has no load
destination. The next instruction uses a mapped carry constant, not the
previous carry, and does not select D. It overwrites the ALU flags and Y with
equal results. The final branch is unconditional and identical on both paths.
Thus neither the first flags nor the first Y control a later internal decision
within these tails under the tested mapping and scenario.

The fixtures are finite, with the same register ranges and limitations as the
fragment study. They do not establish equality for alternative wiring or
external state that the emulator does not represent.

## Main-runner witnesses

A separate replay uses candidate layout 2, R0=55, R12=00, R15=5A and Q=A5
(hex), constant external D=FF, and initial carry 1. Conditions are fixed
per-select inputs, dispatch uses a constant index, and no output writes are
configured. Both local tail starts execute 64 instructions without model
errors. Their first Y values are FF and 00; all 61 trace records after joining
at 07B are identical, and both end at 084 with equal internal state.

The conditional wrapper is also exercised through the main runner:

| Select 2 input | Executed path before reaching 07B | Cycles |
| --- | --- | --- |
| 1 | 256 → 2D9 → 2DA → 2DB | 4 |
| 0 | 256 → 257 → 2DC → 2DD → 2DE | 5 |

The wrapper replays stop on arrival at 07B and have equal PC, stack, RAM, Q,
last ALU results/flags and carry feedback. They are compared at the join, not
at equal elapsed time. The extra branch on the second path costs one cycle.
No sample clock, DAC timing, or real meaning of select 2 is inferred from it.

## Consequences for program interpretation

In the current model, a consumer must observe the first Y during that
microinstruction if the one-unit numerical difference is to matter. A physical
output latch is one possible explanation, but no strobe or destination has
been identified. External timing could also make the extra cycle significant.
Alternatively, the no-load decode or another assumed field could be wrong.

This result is a concrete missing-I/O constraint: claiming that these tails
round or adjust a stored/transmitted sample requires identifying an output
consumer or revising the decode. Adding a PC-keyed capture would demonstrate
an invented consumer, not establish one. This study therefore adds none.

The local starts do not increase reset coverage or explain how the disconnected
fragments are entered. The full plan remains incomplete.

## Reproduction

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/fragment_study.py \
  --out /tmp/nokia-fragments
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/tail_convergence.py \
  --out /tmp/nokia-tail-convergence
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -p 'test_*.py'
```

[Configuration](tail-convergence.json), [replay report](results/tail-convergence/report.json),
and the [expanded fragment report](results/fragment-study/report.json) preserve
the assumptions and comparisons. Four replay directories retain exact mapping,
scenario, summary, trace and empty I/O log. All 22 result files reproduce byte
for byte; all 60 functional/assumption tests pass, including the extended
nonzero/wraparound checks of flags and state convergence.
