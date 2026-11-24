# Split-slice controls at reached 3C5/3DA calls

The [reached-call study](PHOTO-TABLE-CALLERS.md) used one shared nine-bit
instruction for both Am2901 slices. Two [photo-visible facing-pad candidates](PHOTO-SLICE-LINK.md)
instead suggest U8 I4 may follow U2 I1 and U8 I6 may follow U2 I2. The
existing [split-slice model](SPLIT-SLICE-PROBE.md) supports that hypothesis.
This experiment applies it to the 3C5/3DA calls reached from reset.

[`photo_split_callers.py`](photo_split_callers.py) uses all five photo-based
field mappings, E4=I7=A0 high, E2=I0=A1 low, four constant external-D
values, and scenario seeds 11 and 14. Those seeds are the only ones to reach
these tables in the prior 0–15 sweep. Each of the 40 matched cases runs three
versions for 1,000 real-PROM instructions: shared controls, split controls
with undriven shift fill 0, and split controls with fill 1. All use the same
explicit Am2901B ripple flag model, initial RAM/Q, branch policy and dispatch
table. No table entry, RAM value or return PC is injected.

| Mapping | Shared: nonzero source / changed output | Split: nonzero source / changed output |
| --- | ---: | ---: |
| q1 | 25 / 20 | 28 / 24 |
| q2 | 25 / 18 | 28 / 24 |
| q3 | 25 / 20 | 28 / 24 |
| q4 | 21 / 16 | 28 / 24 |
| fitted-swapped | 25 / 17 | 28 / 24 |

Each denominator is 28 reached calls across the eight D/seed cases per
mapping. The split model changes caller state **before** the table as well as
the table arithmetic. For q3, D=`01`, seed 11, the first `3D7` call has source
pair `(0001,0102)` under shared controls and `(00F1,F1F2)` under the
candidate split controls. All three models visit the same table sites and
entries at the same cycles in every matched case, then end at `084`.
Neither split run requests an undriven cross-slice shift bit, so fill 0 and 1
give identical traces.

The split results do not recover a simple sign-selection or quarter-turn
function: across all five mappings, **0 of the nonzero-source calls** leave
the whole output pair equal to either formula. The shared-control matches
remain the narrow counts in the [prior report](results/photo-table-callers.json).
The [saved comparison](results/photo-split-callers.json) contains every reached
source pair, before/after output, call site and trace digest.

This is a sensitive mapping test, not a modem-function identification. The
facing-pad connections have unmeasured gaps; branch decisions and dispatch
indices are scenario inputs; external D is a constant stub. The calls still
belong to a finite reset prefix that ends at the `084` self-loop, and their
output registers have no traced DAC route. The next useful physical or
photo-based constraint is the remaining U8 instruction input assignment and
its clock phase. A controller-driven transmit or receive path must then be
tested through the actual control flow.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/photo_split_callers.py
```
