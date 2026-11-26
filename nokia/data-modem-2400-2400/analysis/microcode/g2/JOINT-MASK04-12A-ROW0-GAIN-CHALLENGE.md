# Frozen row-output phase gates fail at low line level

The [row-0 Boolean holdout](JOINT-MASK04-12A-ROW0-BOOLEAN-HOLDOUT.md)
predicted an unseen phase state and recovered two fresh payloads at
R1 offsets 24/88 and nominal line gain. This challenge keeps those
two phase-output gates, the `3ED` row-0 and `3F8` Y capture visits,
DAC bus, line filter and zero-run gain calibration fixed. It offers
another new eight-byte source payload in each selector mode and runs
the real q3/mask-04 PROM Tx→line→Rx at offset 24 with 75%, 100% and
125% of that gain.

| Selector | Level | Frozen gate wrong among 64 decisions | Payload dibits wrong | Exact line bytes and aligned modeled 8251/8031 payload |
| --- | ---: | ---: | ---: | --- |
| `40` | 75% | 14 | 14/32 | no |
| `40` | 100% | 0 | 0/32 | yes: `07 B2 59 EC 31 8D C4 6A` |
| `40` | 125% | 0 | 0/32 | yes: `07 B2 59 EC 31 8D C4 6A` |
| `60` | 75% | 10 | 10/32 | no |
| `60` | 100% | 0 | 0/32 | yes: `F1 26 90 4B DA 73 05 BE` |
| `60` | 125% | 0 | 0/32 | yes: `F1 26 90 4B DA 73 05 BE` |

The independent reference decoder is exact in all six runs. At
nominal and 125% level the gate rule also recovers all eight offered
line bytes, and aligned modeled 8251/8031 handoff returns every
source byte with no errors or overruns. At 75% it makes only payload
errors, so neither complete line bytes nor controller payload can be
claimed. Every wrong transition touches a state absent from the
14-state development fit; no transition between two known states is
wrong. The 75% runs expose new states `52` and `5C`. The gate phase
for `5C` agrees with a post-hoc graph, but it assigns phase 2 to
`52`, whose post-hoc phase is 3. At 125% the newly seen `00`, `2C`
and `7D` all receive the post-hoc phases correctly.

Adding all six labelled gain cases *after the test* retains a
zero-conflict, connected four-phase graph with 20 states. Thus the
sampled row/Y feature remains capable of a static phase assignment
under this fixture, but the **frozen compact Boolean circuit is
falsified at 75%**. Any revised gates use these failures as
development data and need a new holdout. No physical AGC or automatic
level adaptation has been established.

The [machine report](results/joint-mask04-12a-row0-boolean-gain.json)
contains every real-PROM trace, multi-visit output, phase decision,
line byte and modeled handoff. The [audit](results/joint-mask04-12a-row0-boolean-gain-audit.json)
records the known-state error split, new-state phase comparison and
source hashes. Reproduce with:

```sh
python3 g2/joint_mask04_12a_row0_boolean_gain.py
python3 g2/joint_mask04_12a_row0_boolean_gain_audit.py
```

C3/G2 remain open. Next test a photo-compatible level or carrier-state
signal that predicts phase for new low-level states, then freeze it
before new data and gain fixtures. The untraced ADC, latch, analog and
serial nets remain labelled assumptions, not a reason to pause.
