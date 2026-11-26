# Frozen row gates transfer to an unseen state at a new carrier start

The [phase-120 replay](joint_mask04_12a_row0_twentytwo_phase120.py)
freezes the [22-state phase gates and +5 line timing](JOINT-MASK04-12A-ROW0-TWENTYTWO-HOLDOUT.md),
then changes both the eight-byte payload and R1 carrier start from 112
to 120. It runs the real q3/mask-04 PROM transmitter and receiver for
both controller selectors. No phase labels, gain, filter or sample shift
were fitted on these streams.

| Selector | Fresh source bytes | Reference wrong / 64 | Gate wrong / 64 | New state `59` symbols |
| --- | --- | ---: | ---: | ---: |
| Call `40` | `2D 91 E6 4B 70 AF 13 C8` | 0 | **0** | 40/65 |
| Answer `60` | `B6 05 D9 32 8F 41 EC 7A` | 0 | **0** | 42/65 |

Both runs recover the exact eight offered line bytes and, with the
aligned modeled external SYNDET schedule, the exact eight source bytes
through modeled 8251/8031 receive logic with zero errors or overruns.
One-bit-early and one-bit-late SYNDET controls fail to recover the source.

The [graph audit](joint_mask04_12a_row0_phase120_audit.py) anchors the
new state against the 22 development phases. Both modes require phase
2 for `59`, exactly what the **frozen** Boolean gates predicted. Every
holdout transition is consistent with the resulting 23-state graph;
there are zero conflicts and the earlier labels remain unchanged. This
is a genuine new-state prediction in this conditional readout, though
only one new state and two payloads were tested.

The phase gates are still external logic applied to bytes produced by
executing the DSC PROMs. This result does not show an executed DSC
receive decision, identify the ADC and row-latch pins, or establish the
RxD/RxC/SYNDET connection to USART 01. Continue with a photo-compatible
capture/serializer circuit and an independent output constraint; keep
C3/G2 active without waiting for continuity measurements.

The [executed report](results/joint-mask04-12a-row0-twentytwo-phase120.json)
retains PROM/PCM/ADC digests, gate states and the modeled controller
handoffs. The [audit report](results/joint-mask04-12a-row0-phase120-audit.json)
records the unseen-state constraint. Reproduce from the microcode
directory:

```sh
python3 g2/joint_mask04_12a_row0_twentytwo_phase120.py
python3 g2/joint_mask04_12a_row0_phase120_audit.py
```
