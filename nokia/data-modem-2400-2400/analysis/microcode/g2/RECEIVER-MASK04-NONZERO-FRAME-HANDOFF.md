# Nonzero first bytes survive the long receive handoff

The [long frame-mode receive test](RECEIVER-MASK04-FRAME-MODE-ZERO-HANDOFF.md)
used eight zero payload octets. The [SYNDET transition screen](RECEIVER-SYNDET-PREAMBLE-TRANSITION.md)
found first payload octets whose scrambled line stream begins with the
same `11` dibit as the reversal preamble. This replay uses one such
octet per controller scrambler delay: `01` for delay 5 and `02` for
delay 18, followed by seven zeros.

Each case runs the mask-`04` joint map for 768,047 real PROM instructions
with 32 reversal symbols, 32 data symbols, complementary ADC samples,
and the hypothetical third-frame-byte `81→A1` input at the symbol
boundary. The frozen two-visit readout recovers all 63 measurable
dibits with no error or unknown decision. Its eight data line octets
match the controller scrambler model:

| Delay / angle | Recovered line octets | Aligned paced 8251/8031 result |
| --- | --- | --- |
| 5 / 75° | `43 5A F1 DF 76 36 49 72` | Consumes all eight; descrambles to `01 00 00 00 00 00 00 00` |
| 18 / 165° | `A7 C2 44 59 72 C7 E5 A4` | Consumes all eight; descrambles to `02 00 00 00 00 00 00 00` |

With the fixture placing external SYNDET before bit 64, both ROM runs
remain in controller state `AF`, as expected for a nonzero first octet.
The first non-`11` dibit occurs one dibit later. A pulse at that
data-dependent bit-66 position shifts the 8251 character boundary:
the first consumed octets become `90` and `A9`, and only seven
characters are consumed in the available run. This supplies a
controller/USART control for the same PROM-derived streams.

The result extends the conditional C3 handoff beyond the zero-run
signature, but does not identify the ADC, frame-byte, latch, serializer,
RxD/RxC or SYNDET wiring. The frame edge is projected to the receive
symbol boundary, and the SYNDET pulse is still supplied by the test.
The [machine report](results/receiver-mask04-nonzero-frame-handoff.json)
contains trace and source hashes. Reproduce from the microcode directory
with `python3 g2/receiver_mask04_nonzero_frame_handoff.py`.
