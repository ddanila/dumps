# The candidate DAC carrier bin comes from the assumed top bit

The [single-B5 test](JOINT-MASK04-PHOTO-B5-TONE.md) found no 2,100 Hz
component in the one photo-suggested DAC input. This
[bit-contribution replay](joint_mask04_dac_bit_contributions.py) decomposes
the *same* real-PROM output into all eight candidate DAC inputs, using the
six surviving bus orders and both candidate latch phases. Both 384,256-word
traces and their captured-sample hashes match the earlier B5 replay.

For each bit, the script computes its weighted complex DFT component at
the expected carrier frequency in samples 64–255. The 192-sample window
places both frequencies exactly on 50 Hz-spaced bins.

| Held D127 input | Expected bin | Full-code amplitude | Assumed DAC code bit 7 | Combined other seven bits |
| --- | ---: | ---: | ---: | ---: |
| A1 tone `88` | 2,100 Hz | 7,835.364 | 7,835.364 | 0 |
| Unmodulated carrier `B0` | 1,800 Hz | 7,873.276 | 7,873.276 | 0 |

These values are identical across the six byte orders and both latch
phases. The decomposition is linear: the eight bit phasors sum to the
full-code phasor. Under every surviving bus order, **Am2901 Y7 is assigned
to DAC code bit 7**. Thus the assumed Y7→sample-latch→DAC MSB route is
the decisive *digital* carrier-bin hypothesis to check in the photos or
against another signal constraint. The lower bits can still affect other
frequencies and waveform shape; zero at these two exact bins does not mean
they are inactive. This result also explains why the visible B5 candidate
cannot verify the line carrier by itself.

The [machine report](results/joint-mask04-dac-bit-contributions.json)
records every source-bit phasor, transition count, bus order, phase, trace
hash and capture hash. The code asserts that all lower-bit amplitudes at
the tested bin remain zero and the top-bit amplitude equals the complete
code. Reproduce from the microcode directory with
`python3 g2/joint_mask04_dac_bit_contributions.py`.

The Y7-to-latch route, latch clock, DAC MSB pin connection and analog
output are untraced. The calculation is on assumed digital DAC codes,
not measured line current. It cannot satisfy C2; a photo-compatible MSB
route and the analog/output behavior still need independent support.
