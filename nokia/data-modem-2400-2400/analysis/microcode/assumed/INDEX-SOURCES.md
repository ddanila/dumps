# Datapath-derived indices at the ROM-backed branches

The runner can now use the preceding executed instruction's ALU-Y output as
a dispatch index, with an explicit initial retained value. This tests a
possible address-building path before 008 and 26F rather than supplying every
index randomly. It does not identify a physical latch or choose a winning
source from coverage alone.

The source change is limited to those two branch sites. Their eight- and
sixteen-entry ROM tables mean the existing index modulo table size selects
three or four low bits. Calls remain scenario-indexed: the physical selector
among the five 16-byte call rows is not known.

## Comparison

Each of four Q-independent mappings is tested with scenario indices, current
ALU-Y, updated Q, and preceding ALU-Y. Every combination runs seeds 0–15 for
1,000 cycles with external D fixed at 00 and 55. These 512 runs finish cleanly.
The comparison uses only 16 seeds, so its coverage numbers must not be compared
as matched results against the earlier 128-seed 91.97% experiment.

| Source | Aggregate words per mapping, across these profiles | Targets observed at 26F |
| --- | --- | --- |
| Scenario | 570 | 200, 230 |
| Current Y | 462–463 | 2C6 |
| Updated Q | 527–528 | 200, 280, 2C6 |
| Preceding Y | 522 | 200, 280, 2C6 |

At 008, scenario indices visit 009, 00D, 013 and 054. Preceding Y visits 009
in all mappings, plus 00B in mappings 1 and 3. These restrictions show the
importance of input state and index selection, but cannot identify the actual
source from constant-input runs. Changing the source also changes random-number
consumption and therefore later scenario choices.

The million-cycle example uses mapping 2, external D=55, seed 2 and preceding
Y. At cycle 95, branch 26F consumes retained Y=AA from the preceding executed
word at 26E. Its low nibble A selects Am27S31 address 0FA. The ROM byte is 00,
which gives target 200 under the declared high-bank assumption. Current Y at
26F is zero and would instead select 0F0, byte C6, hence target 2C6.

This is an inspectable candidate data path, not a measured bus transaction.
The high address bits are still supplied by the scenario. External D is still
a constant rather than a model of RAM/ROM feedback. Every instruction updates
the hypothetical retained-Y value; the real board may have a qualified latch.
Those limitations prevent promoting this source as recovered wiring.

## Configuration and trace contract

`dispatch.source` accepts `previous_y` in addition to `scenario`, `y` and `q`.
A table may override the global choice with `index_source`; the experiment uses
that override to leave all call selectors unchanged. Any previous-Y policy
requires an explicit byte-valued `dispatch.initial_y`. Datapath selectors
require integrated mode.

The previous-Y value is sampled before the current ALU instruction executes.
The current result becomes the retained value for the next cycle. When that
state is enabled, the transition digest includes it and the final summary
records it. Traces at explicitly configured dispatches include the raw
`dispatch_input` and its source as well as the masked entry and selected target.
Existing scenarios retain their summary and trace behavior.

Tests distinguish preceding versus current output, check the initial-latch
case, reject missing initial state, and require integrated execution. The
functional/assumption suite passes 46 tests. Earlier ROM-backed results remain
saved unchanged; this source comparison is not a replacement coverage claim.

## Reproduce and inspect

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/index_study.py \
  --integrated-cycles 1000000 --out /tmp/nokia-index-study
```

[Configuration](index-sources.json), [comparison summary](results/index-study/summary.json),
[mapping-2 preceding-Y results](results/index-study/variant-2-previous_y.json),
[million-cycle run](results/index-study/integrated/summary.json), and
[trace](results/index-study/integrated/trace.jsonl) record the evidence.
Actual call-table row selection, external memory feedback, physical DAC writes
and sample timing remain unresolved. The full plan is still incomplete.
