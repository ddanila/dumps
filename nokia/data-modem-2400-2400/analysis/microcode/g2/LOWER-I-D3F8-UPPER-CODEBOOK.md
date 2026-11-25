# No small single-byte four-way decision in the upper-sensitive D3F8 loop

The [3F9 ROM-feedback witness](LOWER-I-D3F8-ROM-FEEDBACK.md) proves that one
photo-compatible input mapping uses an offered ADC byte to select a real
Am27S31 value, writes Q and RAM, then changes later lookup addresses. That
feedback does not itself identify received bits. The
[codebook screen](lower_i_d3f8_upper_codebook.py) tests whether one reached
state byte at a fixed symbol phase can encode the four transmitted dibits.

It re-executes the real control PROMs for six periodic and four seeded
nonperiodic 16-dibit reference streams. The reference receiver recovers all
streams. Each DSC run selects 24,000 complementary ADC bytes at `D3F8`
under the same inverted-previous-sign, upper-`FD` instruction hypothesis.
At every visit the screen records Y at `3F8–3FA`, Q and all 16 RAM bytes.

For each of 1,500 visit phases, 20 state channels and symbol lags −2…+2,
the screen trains a deterministic byte-to-dibit lookup on three periodic
streams and one nonperiodic stream (48 symbols). It checks three other
periodic and three other nonperiodic streams (72 symbols). Unknown holdout
codes count as errors. Readouts use the current byte, XOR with the same byte
one symbol earlier, or subtraction from it; the learned lookup is limited to
4, 8 or 16 distinct byte values.

| Readout | Max code values | Best training errors / 48 | Best holdout errors / 72 | Exact training candidates |
| --- | ---: | ---: | ---: | ---: |
| Current byte | 4 / 8 / 16 | 32 / 18 / 14 | 55 / 42 / 27 | 0 / 0 / 0 |
| XOR previous symbol | 4 / 8 / 16 | 32 / 28 / 16 | 55 / 54 / 31 | 0 / 0 / 0 |
| Subtract previous symbol | 4 / 8 / 16 | 32 / 32 / 14 | 55 / 55 / 37 | 0 / 0 / 0 |

The [machine report](results/lower-i-d3f8-upper-codebook.json) records the
best codebook, phase, lag, errors, unknown-code count, all candidate counts,
trace digests and source hashes. None of these *single-byte, fixed-phase*
readouts identifies a receive dibit even on training data. This narrows the
meaning of the observed lookup feedback: a decision, if present under this
mapping, must use a different site or a more involved combination of state
and timing. The ADC wiring, instruction and condition hypotheses remain
unverified, and no candidate output has reached USART-01 RxD. C3 remains
open.
