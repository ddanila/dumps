# Four nonzero eight-byte streams pass the conditional PROM-to-controller receive handoff

The [earlier handoff](RECEIVER-MASK04-NONZERO-FRAME-HANDOFF.md) changed
only the first payload byte and followed it with seven zeros. This
[challenge](receiver_mask04_random_payload_handoff.py) freezes the same
two-visit external readout and runs four new eight-byte nonzero
payloads, two per controller scrambler delay. Each payload is encoded
as complementary ADC samples with a 32-symbol `11` preamble, and the
real four-PROM joint mask-`04` microprogram executes 768,047
instructions under the same assumed `81→A1` frame-mode edge.

The readout makes **0 wrong and 0 unknown** decisions among 63
measurable dibits in each PROM run (252 total). It reconstructs all
eight offered line octets in each case. With an external SYNDET pulse
placed before data bit 64, the paced 8251/unchanged 8031 ROM consumes
all eight octets without an overrun and descrambles them to the exact
random payload:

| Delay / carrier | Payload | Recovered line octets |
| --- | --- | --- |
| 5 / 75° | `3B 41 AE EA 37 1C 9A 83` | `39 D4 AE 83 ED 16 79 BA` |
| 5 / 75° | `87 25 F0 FD 07 4D 7B 3C` | `05 D7 30 59 87 65 BB E8` |
| 18 / 165° | `71 46 1A ED CB 9D B4 6F` | `D4 84 12 94 C3 C4 70 1D` |
| 18 / 165° | `DC 8F D6 DF A4 70 FF 9A` | `79 4D EA 56 2B 5E F9 F7` |

For each stream, pulsing SYNDET one bit early or late fails to recover
the payload; the late pulse supplies only seven complete characters.
Using the opposite controller descrambler selector also yields the
wrong plaintext. These controls show that both character alignment
and polynomial selection matter to the observed handoff.

The result extends the conditional receive behavior from training and
first-byte probes to complete nonzero data blocks. It still does not
identify a physical ADC input, the external decision/serializer logic,
RxD/RxC wires or a source for SYNDET. The frame edge and sync pulse
are supplied by the scenario, so C3 remains open. A photo-compatible
capture/serial route or independent timing constraint is the next
test; missing continuity alone does not block it.

The [machine report](results/receiver-mask04-random-payload-handoff.json)
records all PROM trace and ADC hashes, USART/8031 outcomes, controls
and source hashes. Reproduce with
`python3 g2/receiver_mask04_random_payload_handoff.py` from the
microcode directory.
