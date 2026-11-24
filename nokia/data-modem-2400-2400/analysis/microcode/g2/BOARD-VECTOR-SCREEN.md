# One-cycle control-store address vectors after 084

The [board-level handoff](ENABLE-TAKEOVER.md#four-prom-board-replay) showed that
a hypothetical external ten-bit driver can fetch one real-PROM word while
U9's address outputs are disabled. Address `036` was illustrative. This
[bounded screen](board_vector_screen.py) applies the same staged handoff at
the first `084` arrival to **all 76** control-store words that decode as
direct, unconditional BRTs away from `084` under the saved sequencer rule.
Those words encode 54 distinct targets. Each candidate is one external PROM
address for one complete fetch/execute cycle; U9's own PC and stack are
preserved until the fetched instruction changes them.

The board model includes the four dumped PROMs, their four LS374 control
registers, U9 and two separate Am2901 slices. The fixture uses the original
q3 field mapping, photo-informed component topology, TEST=0, external D=0,
unknown power-on RAM/Q and the diagnostic ten-bit address driver. The same
reset prefix reaches `084` at cycle 42 before each candidate. After the
handoff, each run is observed for up to 512 further microinstruction cycles.
All 76 handoffs fetch their selected PROM word, load its encoded target into
U9 and release the external bus without a modeled contention or stack change.

| Result | Candidates | Interpretation in this fixture |
| --- | ---: | --- |
| Return to `084` | 69 | Longest return takes 146 cycles after the vector (`10B`→`148`). |
| Model stop | 7 | Reach POP at `27F` or `2FF` with an unknown return address. |
| Still running at 512-cycle bound | 0 | No one-cycle vector sustains a path in this tested set. |

Only fetched word **`111`**, whose BRT target is `133`, reaches the computed
table-call sites `3D7` and `3C2`, once each; it returns to `084` after 41
post-vector cycles. No candidate visits `392`–`39F`, the old q3 candidate
output-table sites, and thus none produces a Y sequence there. The seven
stops are unresolved stack contexts for those fixtures, not evidence that
the physical board cannot execute the words.

This is a negative screen for **one externally addressed BRT word with
TEST=0 and D=0**. It does not rule out other external address words, a
multiword takeover, changing TEST/D inputs, another field mapping, or a
controller-directed control path. Nor does the available photo evidence
establish that Nokia drives U9 EN or all ten PROM address inputs this way.
The [report](results/board-vector-screen.json) records every fetched address,
encoded target, outcome, visited PCs, table calls, candidate output visits,
PROM hashes and source hashes. It supplies a concrete basis for choosing
the next timing and controller-input experiment without treating `084` as
a goal blocker.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/board_vector_screen.py
```
