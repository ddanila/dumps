# Structurally constrained target pools: 91.48% reset coverage

*Runs under the [shared assumptions](ASSUMPTIONS.md).*

A permissive target hypothesis for 26F, 21F and 2C4 reaches **934 of 1,021 used
words (91.48%)** across 128 reset-based runs. This exceeds the numerical 90%
coverage target under declared assumptions. It does **not** recover the actual
dispatch addresses, command encoding, condition sources or physical I/O.
The full plan remains incomplete.

## Entry classification

The experiment looks for previously unreachable, unreferenced boundaries after
unconditional transfers in bank 200–2FF, excluding skip-reachable words. The
bank range is an explicit hypothesis. Each candidate is analyzed twice: with
an empty stack, and with a synthetic return sentinel to classify whether it
needs a caller. These local probes are diagnostic only; none of their visited
addresses contributes to the reported reset-execution coverage.

The 15 boundaries divide into eight entries safe without a caller and seven
entries that have return paths and need a caller. The two setup words before
26F exactly match those before 008. This supports investigating a related
indirect-address path, but does not establish that either path uses these
candidate pools.

| Source | Selected target pool |
| --- | --- |
| 26F, branch | 200, 217, 230, 256, 258, 280, 2C6, 2CF |
| 21F, call | 221, 22B, 22C, 22D, 2B3, 2BC |
| 2C4, call | 22B, 22C, 22D, 2B3 |

For calls, any candidate whose local graph already reaches the source call
site is excluded as directly recursive. That alone is insufficient: allowing
all other returning targets introduces mutually recursive paths and excessive
nesting. The unrestricted combination produces possible stack overflows at
21F, 223 and 2FE. It is saved as a rejected alternative.

Restricting 2C4 to routines containing no further calls removes those failures.
This is an experimental target constraint, not recovered wiring and not a
runtime stack repair. The selected scenario has a fixed target list at each
source; the runner does not silently skip unsafe choices or synthesize stack
contents. Other bounded associations could also fit the evidence.

## Results and limits

| Scenario | Static reachable words | Static stack exceptions |
| --- | --- | --- |
| Previous exceptional-call hypothesis | 841 | None |
| Unrestricted compatible pools | 1,005 | Overflow at 21F, 223, 2FE |
| Selected bounded pools | 1,004 | None |

The 128 runs use 1,000 cycles each, the same seed range and limit as the prior
suite. They reach 934 words, adding 113 and losing one relative to the previous
822-word result. Maximum observed stack depth is three. Conditions and indices
remain seeded scenario inputs; path changes alter random-number consumption,
so this is matched sampling effort rather than identical external stimuli.

A further million-cycle integrated run with Q-independent layout 2, seed 11,
and external D=55 completes cleanly and saves register/virtual-output traces.
Long execution still does not imply continuous useful modem processing.

The 17 statically unresolved words are:

`03F, 0FA, 0FD–0FF, 287–28A, 2DF, 34F–352, 3BD–3BF`.

They remain explicitly unexplained. Some are possible additional dispatch
entries or tails, but they are not added solely to increase coverage. The
70 statically reachable words not visited by this fixed seed suite remain
separate from those 17 disconnected words.

The entry-role classification is stronger evidence than arbitrary target
injection, but much weaker than recovering the data address source. The
coverage number describes the emulator under this broad hypothesis. It must
not be reported as a percentage of understood modem functionality.

## Implementation and verification

Static `graph` now supports an explicit diagnostic start/initial stack and an
out-of-store return sentinel. Default reset exploration is unchanged. A sentinel
return is recorded separately and never included among reachable ROM words.
Tests distinguish a true return from a terminal loop, validate probe inputs,
and preserve the unrestricted overflow counterexample.

The functional/assumption suite passes 44 tests. The scripts save configuration,
classification evidence, rejected and selected graphs, exact target scenarios,
seeded execution digests and remaining unresolved addresses. The coverage
comparison checks the archived baseline's seed/cycle settings before reuse.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/target_study.py \
  --integrated-cycles 1000000 --out /tmp/nokia-target-study
```

Without `--integrated-cycles`, only classification, graph comparisons and the
short reset suite run. Inspect [configuration](target-pools.json),
[classification](results/target-study/classification.json),
[selected scenario](results/target-study/scenario-bounded.json),
[summary](results/target-study/summary.json),
[selected graph](results/target-study/graph-bounded.json),
[rejected graph](results/target-study/graph-unrestricted.json), and
[integration](results/target-study/integrated/summary.json).

Next work must explain the residual entry points and improve datapath/I/O
interpretation. Passing this numerical coverage target does not complete those
requirements or validate the broad target associations used here.
