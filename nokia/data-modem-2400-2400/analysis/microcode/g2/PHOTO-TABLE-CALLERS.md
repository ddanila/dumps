# Reached calls to the 3C5 and 3DA tables

The [local table test](PHOTO-TRANSFORM-CHECK.md) showed how the photo-based
Am2901 field candidates alter the 3C5/3DA arithmetic. This experiment checks
whether those tables are reached from reset, and what values their callers
actually supply under the same candidate E4/I7/A0 and E2/I0/A1 routes.

[`photo_table_callers.py`](photo_table_callers.py) runs each of the five
photo-constrained mappings with the saved rotation-study branch and dispatch
scenario. It uses 16 scenario seeds and four constant external-D values
(`00`, `01`, `55`, `FF`) for each of two held E4 levels. E2 is held low, as in
the [photo controller-path diagnostic](photo_controller_path.py). Each of the
640 runs starts at reset with zero RAM and lasts 1,000 cycles. The script
reconstructs the RAM state at each reached call and after its four real-PROM
table words. All runs finish cleanly.

| Mapping | E4=0: calls / nonzero sources / changed outputs | E4=1: calls / nonzero sources / changed outputs |
| --- | --- | --- |
| q1 | 28 / 0 / 0 | 28 / 25 / 20 |
| q2 | 28 / 0 / 0 | 28 / 25 / 18 |
| q3 | 28 / 0 / 0 | 28 / 25 / 20 |
| q4 | 28 / 0 / 0 | 28 / 21 / 16 |
| fitted-swapped | 28 / 0 / 0 | 28 / 25 / 17 |

Each 28-call group contains 12 calls at `3C2` to the 3C5 table and 16 at
`3D7` to the 3DA table, covering all four entries. Here “source” means the
candidate 16-bit values at RAM register pairs 4/5 and 8/9; “output” means
pairs 10/11 and 12/13. In the E4-low candidate, I7 selects no RAM write,
so no output changes. E4 high permits writes and usually gives nonzero source
values at reached calls. For example, q3 with external D=`00`, seed 14,
reaches `3D7` at cycle 192 with entry 0, source `(0000,FF00)`, Q=`00`, and
output `(0000,0001)` before the table. Its four words leave output
`(0000,FFFF)`. This is a reached-state result, unlike a locally injected
source-pair fixture.

Only **8 of 64 runs** per mapping/E4 case reach either table: the four D
values with scenario seeds 11 or 14. Every observed table call occurs by
cycle 218. All **640 runs end at `084`** by cycle 1,000. Under the saved
sequencer decode, `084` is a direct, unconditional branch back to `084`;
changing later external-D bytes cannot release that loop. The source values
in one q3, D=`01`, seed-11 call were last written by `115` (R4) and `138`
(R8), both candidate D-consuming instructions. Feeding controller bytes at
those sites would test only this finite reset prefix under the present branch
scenario, not a running transmitter. A different, evidence-supported control
path or sequencer timing hypothesis is needed before interpreting these calls
as steady modem processing.

The original full-word sign-selection formula from the uncoupled local
diagnostic matches only 4/25, 9/25, 4/25, 0/21 and 0/25 calls with nonzero
sources and E4 high, respectively. A quarter-turn of the complete source
words matches only 3/25, 3/25, 3/25, 0/21 and 0/25. These were narrow checks
of the wrong source-byte assumption. The [exact follow-up](PHOTO-TABLE-EXACT.md)
shows that the held coupled-pin fixture instead duplicates each source word's
high byte and selects its sign; that rule matches **all 140 E4-high reached
calls** across the five mappings. This is a concrete arithmetic identification
for the declared mapping, while its physical pin route and modem role remain
unverified.

The saved branch conditions and dispatch indices are scenario inputs, and
external D is a constant stub per run, not a real controller stream. The E4
and E2 latch routes and held levels are photo-informed hypotheses, and the
model still shares instruction controls across both Am2901 slices. Register
pairs 10/12 are not traced to the DAC. The result establishes that these
tables can be reached with nonzero caller state under explicit candidates;
the next discriminating work is to constrain the upstream controller/D path
and the split-slice instruction wiring, then repeat the reached-call check.

The [machine-readable report](results/photo-table-callers.json) includes each
call's site, entry, source, Q, and before/after output pairs.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/photo_table_callers.py
```
