# Frozen row-output phase gates predict an unseen state and recover new payloads

The [multi-visit screen](JOINT-MASK04-12A-MULTIVISIT-PHASE.md) selected
an executed `3ED` row-0 bit at receive visit 46 as one possible seventh
phase-state bit. Its 11-state phase map could not decode new states at
R1 offsets 0/64. I explicitly moved those four failed runs into
development, producing a connected, conflict-free 14-state graph, and
minimized each phase output by product-term count and then literal
count. The resulting gate candidate uses only four of the seven state
bits. Let `s0…s5` be first `3F8` Y5–Y7 and second `3F8` Y7,Y4,Y6;
`s6` is `3ED` row-0 bit 0 at the first capture:

```text
p0 = (!s2 & !s4 & !s6) | (s2 & s3 & s6)
p1 = !s6 | !s2
phase = p0 + 2*p1
dibit = inverse(phase_now - phase_previous mod 4)
```

The frozen inverse maps phase steps `2,1,3,0` to dibits `0,1,2,3`.
These gates reproduce all 14 *development* state phases, but that fit
alone is not validation. I froze the gates before choosing a fifth
eight-byte payload pair and running the real q3/mask-04 PROM Tx→line→Rx
at one-time R1 offsets **24** and **88**, with the same DAC bus,
Q=0.5 line and nominal gain:

| Offset | Selector | Frozen gate decisions | Line bytes | Aligned modeled 8251/8031 |
| ---: | --- | --- | --- | --- |
| 24 | `40` | 64/64 exact | eight exact | `8C 13 E7 5A 20 D9 46 BF`; zero errors/overruns |
| 24 | `60` | 64/64 exact | eight exact | `31 C6 0B F4 A8 57 DE 92`; zero errors/overruns |
| 88 | `40` | 64/64 exact | eight exact | `8C 13 E7 5A 20 D9 46 BF`; zero errors/overruns |
| 88 | `60` | 64/64 exact | eight exact | `31 C6 0B F4 A8 57 DE 92`; zero errors/overruns |

Both new streams contain all four payload dibits and the independent
reference decoder is exact in all four runs. The old six-bit lookup
leaves **all 64** decisions unknown in each, while the frozen 14-state
row-0 lookup leaves 12–54 unknown. The Boolean gates decide them all.
They encounter state `6C`, absent from development, and predict phase
1; the phase graph built *after* the holdout also assigns it phase 1
without conflict. This is a genuine unseen-state prediction, though
only one of the 114 previously unobserved seven-bit states is tested.

The [gate fit](results/joint-mask04-12a-row0-boolean.json), fresh
[offset-24](results/joint-mask04-12a-row0-fresh-24.json) and
[offset-88](results/joint-mask04-12a-row0-fresh-88.json) real-PROM
reports, and [holdout audit](results/joint-mask04-12a-row0-boolean-fresh-audit.json)
record the exact capture states, decisions, line bytes, modeled
controller handoff, graph check and source hashes. Reproduce with:

```sh
python3 g2/joint_mask04_12a_row0_boolean.py
python3 g2/joint_mask04_12a_row0_boolean_fresh.py
python3 g2/joint_mask04_12a_row0_boolean_fresh_audit.py
```

This is a stronger conditional explanation of how the executed receive
loop can expose DPSK phase information to a small external circuit.
The `3ED` row-0 output, its latch edge, ADC input route, Boolean gates,
RxD/RxC and SYNDET connections are **not identified board nets**. The
R1 offsets are diagnostic interventions. C3/G2 stay open. Next test
gain, carrier drift and different data with the gates frozen, and
seek a photo-compatible latch/serializer path that actually delivers
these decisions to USART-01.
