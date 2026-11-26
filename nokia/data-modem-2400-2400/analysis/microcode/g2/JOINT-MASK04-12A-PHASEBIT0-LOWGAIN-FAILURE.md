# Unseen-state low-gain failure of the frozen phase-bit-0 circuit

The [two-term phase-bit-0 veto](JOINT-MASK04-12A-PHASEBIT0-VETO.md)
passed new payloads at the previously observed phase-131 gain
settings. It still had 14 changed-mode state-code predictions that no
saved real-PROM capture had tested. This challenge froze the veto,
changed the carrier start to **133**, used two new eight-byte payloads,
and set the assumed receive gain to **0.8×** its calibrated value.
The [matched control](joint_mask04_12a_phasebit0_veto_baseline133_control.py)
reruns the same carrier and payloads at the original gain.

| Selector | Receive gain | New state `1D`? | Veto errors | Old 12-state cover errors | Modeled clipping | Controller source bytes |
| --- | ---: | --- | ---: | ---: | ---: | --- |
| Call `40` | 1.0× | No | **0/64** | 0/64 | 0 | Exact eight |
| Answer `60` | 1.0× | No | **0/64** | 0/64 | 0 | Exact eight |
| Call `40` | 0.8× | **Yes** | **4/64** | 0/64 | 0 | Wrong |
| Answer `60` | 0.8× | **Yes** | **7/64** | 0/64 | 0 | Wrong |

The [matched audit](joint_mask04_12a_phasebit0_veto_lowgain133_matched_audit.py)
confirms identical offered payloads, real-PROM transmitter trace,
candidate raw DAC bytes and receiver PC-path digest between each gain
pair. Only the modeled PCM and receiver trace change. There is no
modeled clipping in either setting. The independent reference decoder
misses three call dibits and zero answer dibits at **both** gains; that
result does not explain the veto's additional low-gain failure.

The [new-state audit](joint_mask04_12a_phasebit0_veto_lowgain133_audit.py)
finds four call and seven answer adjacent-transition constraints that
all assign previously unseen code `1D` phase **0**. The old cover
predicts 0, while both the original photographed-package circuit and
the frozen two-term veto predict **1**. Every wrong veto decision
crosses into or out of `1D`. The modeled serial handoff still emits
bytes without controller errors or overruns, but those bytes do not
match the offered line or executed controller payload. This is a
negative unseen-state holdout for the proposed external logic.

Under the direct seven-state-bit-plus-mode inputs, the shortest single
product term that could clear bit 0 at `1D` **without clearing any
previously correct observed bit-0 label** needs four literals. That
is a constraint on a further fitted patch, not evidence that such a
gate is physically connected. A third per-state veto would remain
unverified on other gain and carrier conditions.

The [0.8× challenge](results/joint-mask04-12a-phasebit0-veto-lowgain133-challenge.json),
[1.0× control](results/joint-mask04-12a-phasebit0-veto-baseline133-control.json),
[new-state audit](results/joint-mask04-12a-phasebit0-veto-lowgain133-audit.json)
and [matched audit](results/joint-mask04-12a-phasebit0-veto-lowgain133-matched-audit.json)
preserve the actual PROM captures, trace and PCM hashes, phase
constraints, wrong indices and controller bytes. Reproduce from the
microcode directory with:

```sh
python3 g2/joint_mask04_12a_phasebit0_veto_lowgain133_challenge.py
python3 g2/joint_mask04_12a_phasebit0_veto_baseline133_control.py
python3 g2/joint_mask04_12a_phasebit0_veto_lowgain133_audit.py
python3 g2/joint_mask04_12a_phasebit0_veto_lowgain133_matched_audit.py
```

C3 and G2 remain open. The next test should examine a richer,
photo-compatible state or timing input at the same matched low-gain
fixture, and demand transfer across both low and high gain on a fresh
real-PROM holdout. Keep the DAC/ADC, mode, logic and serial nets as
labelled assumptions; missing continuity is not a goal blocker.
