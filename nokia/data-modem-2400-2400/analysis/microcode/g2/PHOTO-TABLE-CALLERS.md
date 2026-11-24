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

The reached results do not establish a simple sign selection or quarter-turn.
Among calls with nonzero sources and E4 high, the exact sign-selection formula
from the uncoupled local diagnostic matches only 4/25, 9/25, 4/25, 0/21 and
0/25 calls respectively across the five mappings. The quarter-turn formula
matches only 3/25, 3/25, 3/25, 0/21 and 0/25. These counts compare the
*whole output pair* after the call; prior output state and the current Q may
also matter. They are narrow checks of those formulas, not identifications of
the actual table function.

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
