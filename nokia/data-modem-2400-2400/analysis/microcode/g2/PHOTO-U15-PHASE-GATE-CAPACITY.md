# Can the photographed U15 express the candidate receive phase gates?

The DSC2847 [component photo](../board/evidence/front-rectified.jpg) marks
U15 `SN74S64J` and shows seven pins on each side. The
[TI data sheet](https://www.ti.com/lit/ds/symlink/sn54s64.pdf) confirms a
14-pin 4-2-3-2 input AND-OR-INVERT gate:
`Y = NOT(ABCD + EF + GHI + JK)`. The [inventory](../board/inventory.json)
has been corrected from 16 to 14 pins. This part is a plausible logic
resource; its signal connections and actual role are not visible enough
to assign.

The [capacity search](photo_u15_phase_gate_capacity.py) uses the 22
observed `01`-mode phase labels and 12 observed `81/A1`-mode labels.
It supplies seven captured state bits plus a **hypothetical** mode bit 7
(`01→0`, `81/A1→1`) to U15. For each phase output and its complement,
it exhausts every one- through four-literal cube over those eight inputs,
rejects any cube hitting an observed opposite-label state, and tries
every assignment to the S64's four fixed groups. Unobserved states are
don't-cares. Unused groups are assumed tied low; unused inputs of active
groups are assumed tied high.

| Observed labels supplied | Phase bit 0 on one U15 | Phase bit 1 on one U15 |
| --- | --- | --- |
| `01` mode alone, 22 states | Fits in either output polarity | Fits |
| `81/A1` mode alone, 12 states | Fits in either output polarity | Fits |
| Both modes, with direct mode bit | **No fit** in either output polarity | Fits |

For the combined labels, one exact phase-bit-1 witness is
`P1 = NOT[(s2 AND mode) OR (s2 AND s6)]`. Its two two-input terms fit
the S64's available groups, with the other two disabled. The result
only proves Boolean capacity on the observed states. It does not show
that U15 receives `s2`, `s6` or the mode signal, or that its output is
one of the actual modem phase bits.

The phase-bit-0 no-fit has a precise scope. Even if all four S64 groups
could accept four inputs, its direct AOI form needs at least **five**
product terms on these 34 labels. Its complemented output needs four
terms of widths 4, 3, 3 and 2, but the S64 provides only one four-input
and one three-input group. Input preprocessing, a second gate package
or another state signal could change this result. A direct U15-only
implementation of both mode-conditioned phase outputs is therefore
excluded under the stated eight-input hypothesis, not excluded for the
board as a whole.

The [machine report](results/photo-u15-phase-gate-capacity.json) saves
every fit, candidate-mask counts, gate assignments, the no-fit result
and source hashes. Reproduce from the microcode directory with:

```sh
python3 g2/photo_u15_phase_gate_capacity.py
```

C3 and G2 stay open and active. Next test a photo-compatible U15/U21/U19
two-stage phase-bit-0 route, including its output polarity and clock
arrival at the assumed serializer. Keep the board nets labelled as
assumptions until another observation constrains them.
