# The frozen `3F9` feature does not rescue the ROM-sensitive loopback

This [test](joint_mask04_12a_3f9_gap_test.py) carries the independently
frozen [16-key `3F9` transition table](RECEIVER-MASK04-3F9-3FA-FEATURE-SCREEN.md)
into the [controller-buffered `12A` DAC loopback](JOINT-MASK04-12A-BUFFERED-LINE.md).
It reruns both real-PROM transmitters and receivers under the same
candidate bus, analog filter, six-sample alignment and complementary
ADC schedule. Transmitter, receiver, PCM and ADC hashes all match the
prior loopback. The offered dibits are used only for scoring; no
loopback labels are added to the table.

| Selector | Known wrong / unknown among 32 data dibits | Previously unanswerable gaps rescued |
| --- | ---: | ---: |
| Call `40` | 3 / 24 | 0 of `8, 14, 29` |
| Answer `60` | 7 / 24 | 0 of `10, 12, 13, 17, 31` |

The independent training fit and its zero-known-error holdout score
therefore do not carry over to this modeled DAC→ADC waveform. The
`3F9` output is input-sensitive, but the fixed `46/93` two-bit
lookup is too sparse or differently quantized here. A selector over
this lookup and the three old fixed pairs still has no answer at the
four all-unknown positions. This is a failure of the stated feature,
line fixture and readout, not proof that the DSC lacks a receive
decision path.

Next compare the raw ADC codes and executed `3F9`/`3FA` keys at those
four loopback positions with independent training and holdout streams.
Then test a photo-compatible gain/phase or multi-sample circuit on a
new independent fixture before rechecking the buffered line. The
gate, DAC/ADC buses and RxD route remain assumptions; C3 and G2 stay
open without waiting for pin continuity.

The [machine report](results/joint-mask04-12a-3f9-gap-test.json)
records the paired hashes, all 32 predictions and exact remaining
gaps. Reproduce with `python3 g2/joint_mask04_12a_3f9_gap_test.py`.
