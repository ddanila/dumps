# Frozen receive readout with carrier-frequency offset

The [dual-feature readout](RECEIVER-MASK04-DUAL-FEATURE-CONSENSUS.md) had
previously been checked against fixed carrier-phase rotations. This
[experiment](receiver_mask04_frequency_offset.py) changes the transmitted
carrier frequency while leaving the receiver's two capture visits, both
decision tables and consensus rule frozen. The 1,800 Hz reference receiver
decodes every test input before PROM execution, so the injected PCM remains a
valid signal for this fixture.

Each case has a 32-symbol `11` preamble, 16 seeded data symbols and eight
trailing symbols for pulse shaping. The candidate joint mask-`04` map executes
576,047 real-PROM words and accepts 18,000 complementary ADC visits per case.
The readout uses executed `3F8` Y bytes at symbol-relative visits 47 and 94.
The initial phase is 75° or 165°; carrier offsets are −7, 0 and +7 Hz. A
7 Hz offset accumulates about 101° of carrier phase across 48 captured
symbols, so this tests drift during the stream rather than another fixed
rotation.

| Carrier offset | Initial phases | Wrong / measurable dibits | Undecided dibits | Undecided data dibits |
| --- | --- | ---: | ---: | ---: |
| −7 Hz | 75°, 165° | 0 / 94 | 2 | 0 |
| 0 Hz | 75°, 165° | 0 / 94 | 0 | 0 |
| +7 Hz | 75°, 165° | 0 / 94 | 6 | 3 |

The two readouts have no conflicting known decisions. The negative offset
keeps all 32 data decisions across both phases, while the positive offset
leaves three of those decisions unknown. Thus the current frozen consensus
does not yet provide a complete 2,400-bit/s receive stream at +7 Hz, despite
making no incorrect known decisions. The zero-offset transmitter is checked
sample-for-sample against the prior reference generator.

This is a conditional result under the assumed ADC gate, complementary input,
symbol-relative clocks and readout logic. It does not establish a physical
phase tracker, tolerance across other data/offsets, or the RxD/RxC/SYNDET
route. Keep C3 open. The next bounded test is to capture additional executed
visits around the unknown symbols and test a frozen, photo-compatible
multi-visit consumer on new offset/data fixtures; do not fill unknown labels
from the reference answers.

The [machine report](results/receiver-mask04-frequency-offset.json) records
case metrics and trace/source hashes. Reproduce from the microcode directory
with `python3 g2/receiver_mask04_frequency_offset.py`.
