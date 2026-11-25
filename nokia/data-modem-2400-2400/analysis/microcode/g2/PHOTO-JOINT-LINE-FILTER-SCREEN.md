# One conditional analog line stage preserves tone, silence and data

The [joined PROM run](PHOTO-JOINT-TONE-TRAINING-DATA.md) checks a continuous
A1 tone → A2 capture-off → A3 reversals → A4 data phase path, but its raw
candidate DAC codes are distorted. The [line-stage screen](photo_joint_line_filter_screen.py)
tests one fixed analog hypothesis against that **same** verified stream:
the CD4094-derived A2 capture gate drives the DAC input to mid-code 128,
while a second-order bandpass centered at 1,950 Hz processes the continuous
9,600-sample/s output. The internal phase accumulator continues through A2.
No analog component value, gate wire or line connection is claimed as traced.

The script reconstructs each joined stream from its inputs and checks the
selected-bus sample SHA-256 against the full real-PROM report before filtering.
It then tests all six byte orders that survived independent nonperiodic data
validation, both controller modes, Q values 0.5/1/2/3 and all eight sample
alignments. The bandpass is a fixed biquad, not a trained equalizer.

| Bandpass Q | Late A1 2,100 Hz R² across 12 bus/mode cases | Best common-alignment A3/A4 errors / 744 |
| ---: | ---: | ---: |
| 0.5 | 0.590–0.593 | 0 |
| **1** | **0.721–0.725** | **0** at shift 6 or 7 |
| 2 | 0.835–0.839 | 17 |
| 3 | 0.881–0.885 | 70 |

At Q=1 every bus/mode case retains a 2,100 Hz peak, makes **0/62**
independent matched-filter errors at the same shift 6, and has less than
0.001 of the late-A1 RMS during the last 32 A2 samples. The unfiltered joined
codes previously fit 2,100 Hz with R² 0.286–0.359; the bandpass improves
the candidate tone while preserving the known dibits. A narrower filter
raises tone purity but introduces symbol errors even after testing all eight
shared alignments. That tradeoff is a concrete constraint for a proposed
line filter, not proof of the physical analog transfer function.

The run demonstrates a **conditional complete transmit signal path** under
one clock, one bus, one gate and one filter family. C2 remains open because
the 74LS273/74LS373 clock and full DAC08 wiring, A2 mute mechanism, DAC
current-output conversion and line connector route are not independently
constrained. The [machine report](results/photo-joint-line-filter-screen.json)
records all 48 filter/bus/mode cases, their eight alignments and source
hashes. Reproduce with `python3 g2/photo_joint_line_filter_screen.py` from
the microcode directory. A useful next check is to compare this Q≈1 response
and gate timing with the photographed analog components or an independently
constrained output node.
