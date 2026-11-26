# A Y7-to-Q4 hypothesis makes the visible DAC08 B5 route carry the carrier

The DED 3558 photo suggests a 74LS273 **Q4 pin 9 → DAC08 B5 pin 9**
trace. The [earlier B5 replay](JOINT-MASK04-PHOTO-B5-TONE.md) assumed
Am2901 Y4 reached the latch's D4 input; that B5 bit had **zero power at
2,100 Hz** in the held-tone run. This [alternative route test](joint_mask04_photo_b5_y7_route.py)
instead assumes **Y7 → D4**, with the same photo-suggested Q4→B5
segment. It unpacks and hash-checks the 832 Y7 samples captured from
each 1,248,256-instruction real-PROM call/answer run, then assigns each
bit only DAC08 B5's eight-count weight.

| Candidate B5-only signal | Call `40` | Answer `60` |
| --- | ---: | ---: |
| Late A1 tone peak / sinusoidal R² | 2,100 Hz / 0.958 | 2,100 Hz / 0.958 |
| Direct A3 half-turn error | <10⁻¹¹° | <10⁻¹¹° |
| Direct A4 quadrant errors | 0/32 | 0/32 |
| Filtered A3/A4 dibit errors | 0/62 | 0/62 |
| Late A2/A1 RMS with assumed mid-code gate | 1.58×10⁻⁸ | 1.58×10⁻⁸ |

The direct phase check uses the B5 current step centered around its own
mid-code, not the DAC MSB bit mask used by the earlier phasor diagnostic.
The assumed A2 gate forces B5 to mid-code before the same Q=1 bandpass;
that gate is what makes the silence interval quiet. The result shows
that a route containing the one visible Q4→B5 segment **could** carry
the conditional tone, reversals and data if Y7 drives D4 and the latch
is clocked at the proposed 9,600 Hz. The earlier Y4→D4 negative result
shows the input assignment matters.

This is a scaled replay of the **same executed Y7 samples** used in the
MSB candidate, not independent transmitter evidence. The two complete
DAC-bus hypotheses are alternatives: the six prior survivor orders
assign Y7 to DAC08 B1/MSB, whereas this test assigns it to B5. The
photo supports Q4→B5 only; Y7→D4, latch clock, all other DAC bits,
current conversion, A2 gate, bandpass and line connector remain
untraced. C2 remains open. A next photo-compatible test should constrain
the Y7-to-latch data path or the DAC output node and distinguish B1 from
B5 assignment without assuming the result.

The [machine report](results/joint-mask04-photo-b5-y7-route.json)
contains the PROM sample hashes, tone and phase metrics, receive scores,
photo/source hashes and explicit limitations. Reproduce from the
microcode directory with `python3 g2/joint_mask04_photo_b5_y7_route.py`.
