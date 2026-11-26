# Adjacent receive captures narrow the unseen `1D` timing question

The [phase-133 low-gain challenge](JOINT-MASK04-12A-PHASEBIT0-LOWGAIN-FAILURE.md)
showed that the frozen phase-bit-0 circuit misclassifies new state `1D`.
The [expanded replay](joint_mask04_12a_lowgain133_expanded_visits.py)
re-executes both 0.8× real-PROM call/answer cases and captures `3F8` Y and
row-0 Y at visits `46`, `47`, `93`, `94` and `141`. All original transmit,
receive and PCM hashes, states and wrong-decision indices match the saved
challenge. It finds the same six `1D` symbol occurrences.

The [value audit](joint_mask04_12a_lowgain133_expanded_audit.py) finds:

| Capture | `1D` values | Exact-byte overlap with the 38 other symbols whose modeled phase bit 0 is 1 |
| --- | --- | --- |
| visit `94`, `3F8` Y | `4F` in all six | none |
| visit `141`, row-0 Y | `9F` in all six | `9F` in 24 symbols |
| visit `141`, `3F8` Y | `3F` in four, `4F` in two | none |

The visit-`94` byte is a stable candidate discriminator **in this matched
low-gain fixture**. The visit-`141` row byte cannot by itself separate
`1D` from opposite-bit symbols, and the visit-`141` `3F8` byte is not
constant even within `1D`. None of these observations identifies a physical
latch edge or proves transfer to the saved mode-1 states, which were captured
only at visits `46` and `93`. A new Boolean term fitted from these bytes
would repeat the unseen-state problem. Next capture visit `94` on the
previously passing mode-1 gain/carrier cases, freeze a photo-compatible
consumer, and challenge it on new data and gain.

The [expanded capture](results/joint-mask04-12a-lowgain133-expanded-visits.json)
and [machine audit](results/joint-mask04-12a-lowgain133-expanded-audit.json)
retain the observed values and source hashes. Reproduce from the microcode
directory with `python3 g2/joint_mask04_12a_lowgain133_expanded_visits.py`
and `python3 g2/joint_mask04_12a_lowgain133_expanded_audit.py`. The ADC,
mode, DAC/line, latch and serial routes remain labelled assumptions. C3 and
G2 remain open.
