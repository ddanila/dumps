# Executed candidate transmitter drives the executed receiver

This [loopback run](joint_mask04_tx_rx_loopback.py) joins two previously
separate real-PROM paths under one explicit signal fixture. It takes the
832 Y7 samples already captured from each 1,248,256-instruction
controller-derived A1–A4 transmitter run, assigns them to the
photo-suggested 74LS273 Q4→DAC08 B5 output candidate, gates A2 to
mid-code, and applies the declared 1,950 Hz Q=1 line filter. It then
aligns the resulting A3/A4 PCM by six samples, scales it to ±110, presents
complementary bytes to the candidate ADC input, and executes the same
joint mask-`04` mapping for another **756,047 real-PROM instructions**
per selector. The receiver takes 23,625 ADC samples and reaches all four
receive rows at every sample.

The six-sample alignment leaves 32 A3 preamble symbols and the first
31 A4 data symbols. The independent reference receiver recovers their
62 measurable differential dibits before they enter the receive PROM.
The frozen three-pair ADC-margin readout is then applied to the executed
`3F8`/`3ED` captures without retraining.

| Selector | Reference errors | PROM-readout wrong / unknown / 62 | Opposite-selector data control | Fixed pair 46/93 |
| --- | ---: | ---: | ---: | ---: |
| `40` call | 0 | 0 / 0 | 10 wrong | 0 / 0 |
| `60` answer | 0 | 0 / 0 | 10 wrong | 0 / 0 |

The call and answer receive traces have different digests. The
opposite-selector control scores each frozen output against the other
controller's A4 dibits; all ten differing data dibits are then wrong.
This rules out a constant or label-insensitive readout in this fixture.
The later 94/141 pair alone makes two errors and several abstentions,
so the success does not mean every capture phase works.

This is a joined **digital execution and signal-model result**, not a
verified board-level loopback. The Y7→D4 connection, 74LS273 clock,
DAC08 B5 current path, analog filter, ADC polarity/range and receive
capture/decision circuit are not traced. The two PROM runs are separate
and joined by modeled samples; the last A4 dibit is excluded by the
fixed alignment, and no USART RxD/RxC or external SYNDET signal is
generated here. Thus C2 and C3 stay open. The next high-value test is
to capture the missing post-A4 transmitter samples, carry all 64 A3/A4
symbols into the receiver and test the resulting line bytes through the
preserved 8251/8031 handoff.

The [machine report](results/joint-mask04-tx-rx-loopback.json) records
the transmitter and receiver trace digests, PCM/ADC hashes, every frozen
decision and the opposite-selector control. Reproduce from the
microcode directory with `python3 g2/joint_mask04_tx_rx_loopback.py`.
