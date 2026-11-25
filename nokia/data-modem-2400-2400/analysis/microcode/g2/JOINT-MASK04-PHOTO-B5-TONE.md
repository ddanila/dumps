# The one photo-suggested DAC bit does not carry the carrier peak by itself

The [DED 3558 front photo](../../../photos/PXL_20261123_114854803.jpg)
suggests one short DAC data route, from 74LS273 Q4 pin 9 toward DAC08 B5 pin
9. The whole input bus and the Y-to-74LS273 data route remain untraced.
This [fixed-map replay](joint_mask04_photo_b5_tone.py) tests the conditional
Y4→D4→Q4→B5 assignment on the same lower-mask-`04` mapping used by the
joint transmit/receive work. It runs 384,256 real-PROM instructions for
each of two held D127 inputs: the controller-derived A1 tone step `88`, and
an unmodulated carrier step `B0`. Each captures 256 candidate DAC samples
at both U10 D2 edge phases. All six surviving photo-compatible byte orders
map the same Y4 source bit to DAC code bit 3, so their B5 candidate is
identical.

| Held input | Full candidate DAC code peak, all six bus orders and both latch phases | B5 bit peak in 1–2.6 kHz search | B5 power at full-code peak |
| --- | ---: | ---: | ---: |
| A1 tone step `88` | **2,100 Hz** | 2,400 Hz | 0 at the exact 50 Hz DFT bin |
| Unmodulated step `B0` | **1,800 Hz** | 2,600 Hz | 5.04% of B5's strongest 1–2.6 kHz bin |

The analysis uses the late 192 samples of each run, giving exact 50 Hz DFT
bins. B5 changes 127 times in the 256 tone samples and 255 times in the
unmodulated samples. Its switching is input-sensitive, but **this bit alone
is not an independent carrier witness**: the 2,100/1,800 Hz peaks emerge
from the full assumed DAC code, not from the one visible DAC input candidate.
That does not reject the B5←Q4 route. B5 weighs only eight counts in an
8-bit DAC code, and the higher-weight pins can dominate the analog sum.

The photo suggests only Q4→B5. Y4→D4, the 74LS273 clock, the other seven
DAC input connections, the DAC current-output stage and the line connector
are still hypotheses. C2 remains open. The next useful output-route check
is a higher-weight DAC input or an analog node, tested against both the
2,100 Hz tone and the 1,800 Hz carrier rather than interpreting B5's own
switching as line output. The [machine report](results/joint-mask04-photo-b5-tone.json)
records trace digests, sample hashes, bit transition counts and both phase
spectra. Reproduce from the microcode directory with
`python3 g2/joint_mask04_photo_b5_tone.py`.
