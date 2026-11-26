# New-state phase-125 challenge of the frozen package circuit

The [U13/U15/U19/U21 circuit](PHOTO-U15-U19-U21-PHASE-ROUTE.md) was
frozen after fitting 34 observed mode-conditioned state labels. To test
its prediction beyond those labels, the [challenge](joint_mask04_12a_mode_phase125_challenge.py)
ran two new eight-byte controller payloads through the real-PROM
transmitter, candidate Q=0.5 line, and real-PROM receiver at R1 carrier
offset **125**. The `81→A1` input at `D3EB`, +5 sample shift, DAC/ADC
mapping and 8251/8031 serial timing remained explicit circuit assumptions.

| Real-PROM run | New state | Independent reference | Old 12-state cover | Frozen package circuit | Modeled serial/controller handoff |
| --- | --- | ---: | ---: | ---: | --- |
| Call `40` | `3D` | 0/64 wrong | **14/64 wrong** | **0/64 wrong** | Exact eight line and source bytes |
| Answer `60` | `3D` | 0/64 wrong | **8/64 wrong** | **0/64 wrong** | Exact eight line and source bytes |

The [independent audit](joint_mask04_12a_mode_phase125_audit.py) uses
the known neighboring state labels and the offered dibits to infer
phase **1** for `3D` from 14 call-side and 8 answer-side transition
constraints. The old cover predicts 0; every one of its wrong
decisions crosses into or out of `3D`. The package circuit predicts 1.
Both runs retain the four-row real-PROM path and have no modeled 8251
timing gaps, controller errors or overruns at the aligned clock.

The [run](results/joint-mask04-12a-mode-phase125-challenge.json) and
[audit](results/joint-mask04-12a-mode-phase125-audit.json) preserve the
capture states, decision indices, serial bytes, source hashes and exact
controller results. Reproduce from the microcode directory with:

```sh
python3 g2/joint_mask04_12a_mode_phase125_challenge.py
python3 g2/joint_mask04_12a_mode_phase125_audit.py
```

This is a genuine one-state extrapolation of the frozen circuit under
the assumed line and board route. It strengthens the external phase
logic hypothesis, but does not identify the actual U13/U15/U19/U21
connections, mode source, RxD/RxC or SYNDET wiring. C3 and G2 remain
open. Test a distinct gain/clock condition for further unseen states,
and trace or discriminate the candidate mode/serializer connections.
