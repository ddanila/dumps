# The conditional `12A` line survives reference-receiver oscillator mismatch

The [fixed-gain phase test](JOINT-MASK04-12A-FIXED-GAIN-PHASE.md)
identified a narrow +6-sample line alignment. This
[challenge](joint_mask04_12a_carrier_mismatch.py) keeps that alignment,
the Q=0.5/1950 Hz candidate line filter and the zero-run-calibrated
gain fixed. It replays the same four nonzero controller-fed streams
through the real PROMs and all six photo-compatible DAC buses. The
original transmitter trace and `12A` sample hashes match their saved
holdout runs. Only the external known-carrier reference decoder's
local oscillator changes from 1800 Hz.

| Reference receiver offset | Exact 64-dibit bus/payload streams | Total wrong dibits |
| ---: | ---: | ---: |
| −14 Hz | 24/24 | 0 |
| −7 Hz | 24/24 | 0 |
| 0 Hz | 24/24 | 0 |
| +7 Hz | 24/24 | 0 |
| +14 Hz | 24/24 | 0 |

This demonstrates tolerance of the **external differential reference
decoder** to the tested relative oscillator mismatch on these line
samples. It does not change the DSC transmitter clock or waveform,
measure a physical carrier offset, or test carrier tracking in the
executed DSC receiver. A ±14 Hz local mismatch does not introduce an
error in this Q=0.5 fixture.
C2/C3 remain open and G2 active. Next constrain the sample latch/line
route and test a receiver decision/USART path on fresh legal inputs.

The [machine report](results/joint-mask04-12a-carrier-mismatch.json)
contains all 120 scores, PCM and trace hashes and source hashes.
Reproduce with `python3 g2/joint_mask04_12a_carrier_mismatch.py`
from the microcode directory.
