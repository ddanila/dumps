# Revised row-phase gates recover fresh phase-112 payloads

The earlier [phase-112 challenge](JOINT-MASK04-12A-ROW0-PHASE112.md)
exposed one wrong extrapolation: the frozen 20-state gates assigned state
`5E` phase 1, while the two real-PROM streams required phase 0. I moved
those failed cases into development. The resulting connected 22-state
graph has zero conflicts and keeps every old phase label. The
[revised gates](joint_mask04_12a_row0_boolean_twentytwo.py) fit those
22 states with three product terms for phase bit 0 and the unchanged
two terms for phase bit 1. This fit is development evidence.

The prior +6 sample alignment also made the independent reference decoder
miss 2 call and 1 answer dibits on those development cases. A
[fixed-gain shift screen](joint_mask04_12a_phase112_line_shift.py) tested
+3 through +10 on the same PROM transmitter bytes. Both +4 and +5 are
reference-exact on both development payloads; +5 was frozen for a new
payload pair. The analog sample shift is still an assumed line fixture,
not a traced Nokia clock.

The [fresh holdout](joint_mask04_12a_row0_twentytwo_holdout.py) runs the
q3/mask-04 real-PROM transmitter and receiver on new eight-byte payloads
at R1 offset 112, fixed gain and +5 alignment:

| Selector | Fresh source bytes | Reference wrong / 64 | Frozen gate wrong / 64 | Modeled aligned 8251/8031 |
| --- | --- | ---: | ---: | --- |
| Call `40` | `84 2F D1 6B 09 F5 38 C2` | 0 | **0** | Eight exact bytes, zero errors/overruns |
| Answer `60` | `47 BA 03 E9 5C 16 D0 7F` | 2 | **0** | Eight exact bytes, zero errors/overruns |

The gate recovered all 64 post-initial dibits and the eight offered line
bytes in both modes. The aligned external SYNDET schedule recovers the
source; one-bit-early and one-bit-late schedules do not. The independent
reference's two answer errors show its own decision rule is imperfect on
this payload, while the source-labelled gate result is exact. These
holdouts visit only the 22 development states, so they test fresh data
at the challenged carrier start, not new-state generalization. No
executed DSC instruction or photographed route has been shown to
implement the external phase gates, row capture, or USART serialization.

Next change the carrier start or line level to seek unseen states under
the frozen 22-state gates, and test a photo-compatible row-latch and
RxD/RxC/SYNDET circuit against the same source-labelled stream. Keep
C3/G2 active and the untraced connections as runnable assumptions.

The [fit](results/joint-mask04-12a-row0-boolean-twentytwo.json),
[line screen](results/joint-mask04-12a-phase112-line-shift.json) and
[holdout](results/joint-mask04-12a-row0-twentytwo-holdout.json) retain
the graph, PROM/PCM/ADC digests, decisions, handoff results and source
hashes. Reproduce from the microcode directory:

```sh
python3 g2/joint_mask04_12a_phase112_line_shift.py
python3 g2/joint_mask04_12a_row0_boolean_twentytwo.py
python3 g2/joint_mask04_12a_row0_twentytwo_holdout.py
```
