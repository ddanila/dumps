# Nonzero first bytes survive the long receive handoff

The [long frame-mode receive test](RECEIVER-MASK04-FRAME-MODE-ZERO-HANDOFF.md)
used eight zero payload octets. The [SYNDET transition screen](RECEIVER-SYNDET-PREAMBLE-TRANSITION.md)
found first payload octets whose scrambled line stream begins with the
same `11` dibit as the reversal preamble. This replay uses two such
octets per controller scrambler delay: `01` and `3D` for delay 5,
`02` and `5A` for delay 18, each followed by seven zeros. The latter
two produce a complete initial `FF` line octet, indistinguishable from
the preamble fill if only its bits are observed.

Each of four cases runs the mask-`04` joint map for 768,047 real PROM instructions
with 32 reversal symbols, 32 data symbols, complementary ADC samples,
and the hypothetical third-frame-byte `81→A1` input at the symbol
boundary. The frozen two-visit readout recovers all 63 measurable
dibits with no error or unknown decision. Its eight data line octets
match the controller scrambler model:

| Delay / angle | First payload | Recovered line octets | Aligned paced 8251/8031 result |
| --- | --- | --- | --- |
| 5 / 75° | `01` | `43 5A F1 DF 76 36 49 72` | Consumes all eight; descrambles to `01 00 00 00 00 00 00 00` |
| 5 / 75° | `3D` | `FF AD 2F BA E1 6B D0 AA` | Consumes all eight; descrambles to `3D 00 00 00 00 00 00 00` |
| 18 / 165° | `02` | `A7 C2 44 59 72 C7 E5 A4` | Consumes all eight; descrambles to `02 00 00 00 00 00 00 00` |
| 18 / 165° | `5A` | `FF C2 24 74 F2 C2 F3 72` | Consumes all eight; descrambles to `5A 00 00 00 00 00 00 00` |

With the fixture placing external SYNDET before bit 64, both ROM runs
remain in controller state `AF`, as expected for a nonzero first octet.
The first non-`11` dibit occurs one dibit later for `01`/`02`, and
four dibits later for `3D`/`5A`. Pulsing at those data-dependent
bit-66 or bit-72 positions shifts the 8251 character boundary:
the first consumed octets become `90`/`A9` or the second offered
octets `AD`/`C2`, respectively. Only seven data characters are consumed
in the available run. This supplies a controller/USART control for
the same PROM-derived streams.

The result extends the conditional C3 handoff beyond the zero-run
signature, but does not identify the ADC, frame-byte, latch, serializer,
RxD/RxC or SYNDET wiring. The frame edge is projected to the receive
symbol boundary, and the SYNDET pulse is still supplied by the test.
The [machine report](results/receiver-mask04-nonzero-frame-handoff.json)
contains trace and source hashes. Reproduce from the microcode directory
with `python3 g2/receiver_mask04_nonzero_frame_handoff.py`.
