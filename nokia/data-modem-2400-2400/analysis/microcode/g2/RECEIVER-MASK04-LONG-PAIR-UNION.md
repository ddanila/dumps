# Two ADC sample-edge readouts on long carrier-offset streams

The [96-symbol offset test](RECEIVER-MASK04-LONG-OFFSET.md) left five data
dibits unknown across three offset cases when the frozen receiver read
executed `3F8` Y only at visits 46/93. This
[same-stream replay](receiver_mask04_long_pair_union.py) captures both
46/93 and 47/94, applies the two already frozen decision tables to each
pair, then combines their results conservatively: a known label is used
only when the other pair agrees or abstains. A pair disagreement remains
unknown. Neither lookup table is refitted, and no reference answer is
substituted for an unknown.

All four cases reproduce the earlier trace and ADC hashes exactly. Each
executes 1,152,047 real-PROM words and has 95 measurable dibits after a
32-symbol `11` preamble and 64 data symbols. The conservative pair union
has **0 wrong, 0 unknown and 0 pair conflicts in all 380 decisions** on
those repeated streams. The mixed-edge 46/94 and 47/93 variants often
leave many unknowns, which makes the boundary choice material rather than
an arbitrary one-visit delay.

The [fresh-seed holdout](receiver_mask04_long_pair_union_holdout.py) freezes
the same two pairs and union rule, then runs four new 96-symbol PROM streams
at both ±7 Hz offsets and both initial phases:

| Offset, phase | 46/93 unknown | 47/94 unknown | Pair conflicts | Union wrong / unknown / 95 |
| --- | ---: | ---: | ---: | ---: |
| −7 Hz, 75° | 3 | 4 | 0 | 0 / 0 |
| −7 Hz, 165° | 3 | 4 | 0 | 0 / 0 |
| +7 Hz, 75° | 6 | 3 | 0 | 0 / 1 |
| +7 Hz, 165° | 2 | 4 | 1 | 0 / 1 |

The first +7 Hz unknown is data symbol 60, where both pairs abstain. The
second is data symbol 32, where the pairs disagree; the 47/94 readout's
known label is wrong while 46/93 is correct. The conservative rule preserves
that conflict as unknown. The holdout aggregate is **0 wrong, 2 unknown / 380**,
with both unknowns in data. This supports a complementary two-sample
readout but does **not** establish complete ±7 Hz recovery. The conflicting
boundary also rules out treating every 47/94 known label as a safe fallback.

The ADC route, two symbol-relative latch edges, external decision tables,
symbol memory and RxD/RxC/SYNDET routing are still hypotheses. The tested
logic is an analysis consumer of executed PROM state, not an identified
Nokia circuit. C3 remains open. Next inspect the executed `3F8`/`3ED`
bytes around symbols 60 and 32, seek a physically plausible conflict
signal or additional visit, and freeze that rule before another seed.

The [same-stream report](results/receiver-mask04-long-pair-union.json) and
[holdout report](results/receiver-mask04-long-pair-union-holdout.json) record
per-case metrics, unknown positions, conflicts and trace/source hashes.
Reproduce from the microcode directory with
`python3 g2/receiver_mask04_long_pair_union.py` and
`python3 g2/receiver_mask04_long_pair_union_holdout.py`.
