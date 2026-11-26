# The ROM-sensitive `12A` line candidate reaches the receiver, but the frozen readouts stop short

The [buffered serial handoff](JOINT-MASK04-BUFFERED-SERIAL-HANDOFF.md)
previously joined controller TxD to a real-PROM transmitter and receiver
through a candidate Y7-only line. This
[new replay](joint_mask04_12a_buffered_line.py) substitutes the
ROM-sensitive, counter-qualified `12A` Y byte identified by the
[PROM-gate timing work](JOINT-MASK04-TX-12A-DELAYED-LATCH.md). It keeps
the same one-symbol buffered bit-pair decoder, upper Am27S31 bank,
controller-derived zero-run bytes, A2 mute, analog filter and six-sample
line alignment. The two **1,269,256-word** transmitter trace digests
match the earlier buffered run exactly.

The script tests all six photo-compatible Y-to-DAC bus orders and 14
line alignments from −7 through +6 samples. At the existing +6
alignment, every bus gives the independent known-carrier reference
receiver **1/64 call** and **0/64 answer** wrong dibits. The call error
is at decision index 35. Every tested bus has its best reference score
at +6; an adjacent +5 alignment makes two errors in each mode. This
is a stronger line-level test than the earlier fixed-template A3/A4
score, which reported 0/62 on both modes.

One representative bus then drives a separate real-PROM mask-04
receiver through complementary ADC bytes. Both receiver runs sustain
all selected visits. The previously frozen external readout family
performs as follows on the 32 data dibits:

| Readout | Call wrong / unknown | Answer wrong / unknown |
| --- | ---: | ---: |
| Fixed visits 46/93 | 0 / 9 | 0 / 9 |
| Fixed visits 47/94 | 2 / 7 | 4 / 13 |
| Fixed visits 94/141 | 2 / 15 | 2 / 18 |
| Frozen ADC-margin selector | 2 / 2 | 4 / 2 |

No readout reconstructs all eight line bytes, so this replay does not
offer a complete byte to the paced USART/8031 handoff or advance its
`AF→B0` state. The answer-side line has an exact independent reference
decision, which isolates the remaining failure to the tested PROM
capture/readout family rather than the answer waveform alone. The call
line also needs a one-decision correction or a better analog/timing
route. A new readout must be developed on separate data and then
tested here without using these answer labels as its training set.

All DAC, gate, divider, analog, ADC and USART wires are still explicit
photo-compatible assumptions. The external decision rules are not an
identified board circuit. Thus this result strengthens the conditional
ROM-sensitive C2 signal path but does not pass C2 or C3; it gives a
specific receiver and call-line target without making missing
continuity a G2 blocker.

The [machine report](results/joint-mask04-12a-buffered-line.json)
contains transmitter/receiver trace hashes, line/ADC hashes, all six
bus/shift scores and frozen readout decisions. Reproduce with
`python3 g2/joint_mask04_12a_buffered_line.py`.
