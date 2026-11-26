# Adjacent receive visits under the full-byte carrier-offset fixture

The [full-byte carrier-offset challenge](JOINT-MASK04-FULL-BUS-CARRIER-OFFSET.md)
left gaps in the fixed `46/93` PROM-byte readout. This screen reruns the
same two non-zero payloads at −7, 0 and +7 Hz, with the same full-byte DAC
order, Q=1 line filter, preamble AGC and frozen receive tables. It captures
the executed `3ED` Y bytes at ten predeclared sample-clock visits and
tests eight two-visit pairs. The widened capture does **not** change the
ADC input or PROM execution: each case matches the previous PCM, ADC hash,
PROM trace digest and `46/93` score. The independent reference decoder
again recovers all 64 differential decisions per case.

| Selector | Offset | Fixed `46/93` gaps | Gaps with no correct known result from any tested pair | Fixed-first `47/94` wrong/unknown data dibits |
| --- | ---: | ---: | --- | ---: |
| `40` call | −7 Hz | 5 | 46, 56 | 0/2 |
| `40` call | 0 Hz | 2 | none | 0/0 |
| `40` call | +7 Hz | 7 | 56 | 1/1 |
| `60` answer | −7 Hz | 6 | none | 0/0 |
| `60` answer | 0 Hz | 9 | none | 0/0 |
| `60` answer | +7 Hz | 5 | 39 | 1/2 |

The eight pairs are `45/92`, `46/93`, `47/94`, `48/95`, `46/94`,
`47/93`, `93/140` and `94/141`. A gap is counted as having a correct
candidate only when one of these frozen-table pair readouts emits the
expected dibit. This is a **diagnostic upper bound**, since a working
selector cannot consult the expected dibit. Four gaps across the three
failing offset cases have no correct known candidate at all. Therefore a
selector over only these pairs and frozen tables cannot recover every byte
in these cases, even with an oracle choosing the pair. The zero-offset
controls and answer −7 Hz do admit simple adjacent-pair fills.

The result points beyond capture-visit selection: inspect the actual Y
features at symbols 46/56 (call −7), 56 (call +7) and 39 (answer +7), then
test a phase-aware or multi-sample readout against fresh payloads and
phase starts. An alternative ADC/clock route may also change these bytes.
No physical latch edge, decision gate or USART path is identified here;
C3 and G2 remain open and active.

Run `python3 g2/joint_mask04_full_bus_offset_visit_screen.py` from the
microcode directory. The [machine report](results/joint-mask04-full-bus-offset-visit-screen.json)
records each pair's scores, conflicts, rescued indices, gap candidates,
input/trace hashes and source hashes.
