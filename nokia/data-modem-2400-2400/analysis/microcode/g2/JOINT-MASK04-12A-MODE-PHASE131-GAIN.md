# Matched gain challenge of the frozen receive phase circuit

The [phase-125 run](JOINT-MASK04-12A-MODE-PHASE125-CIRCUIT.md) showed that
the frozen U13/U15/U19/U21 candidate circuit predicted one unseen state
correctly. This experiment holds a new phase-131 carrier start and two
new controller payloads fixed, then compares the original calibrated
receive gain with **1.25×** that gain. Both settings execute the real
transmit and receive PROMs under the same assumed DAC/line/ADC,
`D3EB` mode, capture and serial routes.

| Selector | Gain | New capture states | Reference errors | Prior 12-state cover errors | Frozen package-circuit errors |
| --- | ---: | --- | ---: | ---: | ---: |
| Call `40` | 1.00× | `4C` | 2/64 | 0/64 | **0/64** |
| Answer `60` | 1.00× | `4C` | 0/64 | 0/64 | **0/64** |
| Call `40` | 1.25× | `2F`, `42`, `48`, `5D` | 2/64 | 21/64 | **16/64** |
| Answer `60` | 1.25× | `2F`, `42`, `48`, `5D` | 0/64 | 18/64 | **10/64** |

The [matched audit](joint_mask04_12a_mode_phase131_gain_audit.py) confirms
identical offered payloads, real-PROM transmitter trace and raw DAC bytes
between each gain pair. The receive PCM and receiver trace change, but
the receiver PC-path digest remains identical. At baseline gain, 12 call
and six answer adjacent transitions independently assign new state `4C`
phase **1**, agreeing with the frozen circuit.

At boosted gain, **all** 65 captures in each run belong to the same
four previously unseen states. Their expected transitions form a
zero-conflict phase graph. With `48=0` as an arbitrary anchor, its
relative labels are `42=1`, `5D=3`, `2F=2`. The frozen circuit's
relative labels are different, so no global phase rotation rescues it.
The modeled serial handoff emits eight bytes in each run, but neither
byte sequence matches the offered line data. The executed controller
therefore receives wrong payload bytes. This is a real negative result
for the fixed circuit and gain/line assumptions, not a C3 pass.

The [U15 capacity screen](joint_mask04_12a_mode_phase131_gain_audit.py)
adds prior `3D` and baseline `4C` labels and tries all four possible
absolute rotations of the boosted-gain graph. For every rotation, a
single U15 still cannot compute phase bit 0 from the seven direct
state inputs plus mode. This excludes only that direct single-package
route; a revised multistage circuit or another capture point remains
possible. The boosted-gain graph cannot be anchored absolutely because
its state alphabet is disjoint from the prior captures.

The [gain fixture](results/joint-mask04-12a-mode-phase131-gain-fixture.json),
[boosted run](results/joint-mask04-12a-mode-phase131-gain-challenge.json),
[baseline control](results/joint-mask04-12a-mode-phase131-baseline-control.json)
and [audit](results/joint-mask04-12a-mode-phase131-gain-audit.json)
preserve the real-PROM captures, hashes, decisions, serial bytes and
limits. Reproduce from the microcode directory with:

```sh
python3 g2/joint_mask04_12a_mode_phase131_gain_challenge.py
python3 g2/joint_mask04_12a_mode_phase131_baseline_control.py
python3 g2/joint_mask04_12a_mode_phase131_gain_audit.py
```

C3 and G2 remain open. The next discriminating test is a gain sweep at
the **same** carrier/payloads to locate the first capture-state switch,
paired with a changed capture bit or timing control. Keep all board
nets labelled as assumptions; do not wait for continuity data before
testing the alternate route.
