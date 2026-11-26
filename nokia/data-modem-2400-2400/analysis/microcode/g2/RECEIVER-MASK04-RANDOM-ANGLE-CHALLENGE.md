# Frozen receive rule survives two more carrier angles

The [random payload handoff](RECEIVER-MASK04-RANDOM-PAYLOAD-HANDOFF.md)
tested four complete nonzero eight-byte streams at 75° and 165°. This
[challenge](receiver_mask04_random_angle_challenge.py) reuses those four
payload seeds, but rotates the candidate ADC input to 15° and 105°.
The primary and alternative decision tables, two-visit `3F8` capture,
32-symbol `11` preamble, and assumed `81→A1` frame edge are unchanged.
Each case executes 768,047 real four-PROM instructions.

| Scrambler delay | Angle | Measurable dibits | Recovered line bytes |
| --- | ---: | ---: | ---: |
| 5 | 15° | 63/63 | 8/8 |
| 5 | 105° | 63/63 | 8/8 |
| 18 | 15° | 63/63 | 8/8 |
| 18 | 105° | 63/63 | 8/8 |

The frozen consensus makes **0 wrong and 0 unknown decisions** in 252
measurable dibits. All 32 reconstructed line bytes equal those offered
to the ADC model. These four new angle/payload combinations extend the
conditional receive result beyond the original carrier pair; they do
not test noise, arbitrary carrier phase, or a physical input route.

The existing board photos support a `3F8` gate-edge capture hypothesis,
but do not trace a complete decision/serializer path into USART-01
RxD/RxC, or the source of SYNDET. The `3F8` consumer and frame edge here
remain explicit external assumptions. C3 stays open; test a
photo-compatible latch/serializer and clock route without treating the
untraced net as a goal blocker.

The [machine report](results/receiver-mask04-random-angle-challenge.json)
contains each offered and recovered byte, score, PROM/ADC hashes, and
source hashes. Reproduce from the microcode directory with
`python3 g2/receiver_mask04_random_angle_challenge.py`.
