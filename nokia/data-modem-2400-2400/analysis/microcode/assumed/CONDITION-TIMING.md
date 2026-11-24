# Select-zero nonzero condition experiment

*Runs under the [shared assumptions](ASSUMPTIONS.md).*

The [Q-independent decode](Q-INDEPENDENT.md) makes the local 1E9 loop
consistent with a current nonzero test. This experiment applies that source
to every conditional select-zero instruction, comparing current and previous
ALU flags. Both timings survive the tested control-flow checks; neither is
identified as the hardware timing.

## Scenario and runner change

The existing `flags` condition mode now accepts `random` as a per-select source.
This allows select 0 to use the zero flag with inverted polarity while selects
1–7 remain seeded random inputs. Select-zero BSR/BRT remain unconditional under
the saved branch hypothesis; only TSK and BLT consult the new flag source.
Dispatch indices still come from the scenario. Unknown flags still use the
explicit fallback already recorded in the scenario.

[condition-search.json](condition-search.json) records four external-read
profiles (00,01,55,FF), 32 seeds, two flag timings and a 1,000-cycle limit.
All four Q-independent mappings are tested. Each comparison aggregates its own
128 runs; coverage from incompatible hypotheses is not merged into one score.
Changing a condition from random to a flag also changes random-number
consumption, so identical seeds across policies do not hold all later random
choices fixed. No hardware inference is drawn from such paired seed paths.

## Results

All **1,024 short runs**, totaling 1,024,000 cycles, finish without stack errors.
Aggregate visited words for each mapping/timing are:

| Mapping | Current flags | Previous flags |
| --- | --- | --- |
| Q-independent 1 | 517 | 477 |
| Q-independent 2 | 489 | 502 |
| Q-independent 3 | 517 | 477 |
| Q-independent 4 | 489 | 477 |

The store has 1,021 used words. These runs do not improve on the earlier
55.34% coverage result. Coverage ranking also changes with the mapping: a
preference based only on the number visited would pick different timings for
different candidates. This is not sufficient to recover the multiplexer.

Two additional million-cycle runs use mapping 2, seed 11, external D=55,
one for each timing. Both complete cleanly. Reports retain terminal PCs,
per-loop visit counts, stack depth, coverage and transition digests. They do
not equate finishing the cycle budget with terminating every routine or
processing a valid modem signal.

The runner's historical modes remain compatible. Tests verify that all-random
flag sources reproduce the ordinary random mode's transitions and final state,
and that select-zero unconditional calls remain unconditional even when the
ALU result is zero. A select-zero TSK in the same fixture uses the flag.
The functional/assumption suite passes 37 tests.

## Reproduce

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/condition_study.py \
  --integrated-cycles 1000000 --out /tmp/nokia-condition-study
```

Without `--integrated-cycles`, only the short comparison runs execute. Saved
[summary](results/condition-study/summary.json),
[current mapping-2 comparison](results/condition-study/variant-2-current.json),
[previous mapping-2 comparison](results/condition-study/variant-2-previous.json)
and [long integrations](results/condition-study/integration.json) preserve both
alternatives. Each long run saves its complete mapping and scenario.

## Remaining constraints

The condition experiment leaves the unresolved address sources unchanged.
At 008, the fallback target 300 bypasses the small routines in 009–06E. Several
of those routines end at a shared tail, and 036 precedes three direct branch
entries (037–039). That structure deserves a separate dispatch hypothesis;
this experiment does not silently add those targets. Likewise, computed calls
21F and 2C4 still use explicit placeholder tables. These address-source gaps,
not another increase in cycle count, are the next route to broader coverage.
