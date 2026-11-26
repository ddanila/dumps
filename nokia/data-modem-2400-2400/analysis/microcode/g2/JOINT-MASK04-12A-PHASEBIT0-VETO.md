# Frozen two-term correction for the receive phase-bit-0 output

The [gain graph](JOINT-MASK04-12A-MODE-PHASE131-GAIN-SWEEP.md) found a
consistent phase label for every captured state across the tested
receive-gain settings. The photographed-package candidate circuit
misses only `48` (needs phase 2, predicts 3) and `2F` (needs phase 0,
predicts 1): both errors are in phase bit 0. A [one-wire and
one-visit screen](JOINT-MASK04-12A-PHASE131-CAPTURE-CONTROLS.md)
did not repair them. This experiment leaves the original phase-bit-1
output unchanged and adds a **hypothetical**, mode-qualified external
veto to phase bit 0:

```text
veto_2F = s0 AND s1
veto_48 = (NOT s1) AND (NOT s2) AND s6
P0_new  = P0_original AND NOT(mode AND (veto_2F OR veto_48))
P1_new  = P1_original
```

The [frozen model](joint_mask04_12a_phasebit0_veto.py) matches all 22
observed `01`-mode and 20 `81/A1`-mode state labels. It replays **22
saved real-PROM streams**, 1,408 dibits, without an error. Those
streams helped select the terms; this is development evidence. The
veto changes 16 of 128 possible mode-`81/A1` state codes, including
14 unobserved codes, and leaves mode `01` predictions unchanged.

The correction was frozen before four new two-selector fixtures were
run through the real transmit and receive PROMs and the modeled
8251/executed 8031 serial handoff. The [independent holdout audit](joint_mask04_12a_phasebit0_veto_holdout_audit.py)
separates fixtures that actually exercise a veto term:

| New payload fixture | Veto exercised? | Original package errors, call/answer | Corrected errors | Modeled clipping, call/answer | Line and controller bytes |
| --- | --- | ---: | ---: | ---: | --- |
| Phase 137, 1.15× | No | 0/64, 0/64 | **0/64, 0/64** | 0, 0 | Exact |
| Phase 139, 1.15× | No | 0/64, 0/64 | **0/64, 0/64** | 0, 0 | Exact |
| Phase 131, 1.15× | **Yes: `48`** | 17/64, 12/64 | **0/64, 0/64** | 0, 0 | Exact |
| Phase 131, 1.25× | **Yes: `48`/`2F`** | 15/64, 17/64 | **0/64, 0/64** | 4, 2 | Exact |

All four fixtures use new eight-byte payloads in both selectors.
Their real-PROM receiver PC path sustains, and the corrected aligned
serial replay has no unknown RxC edges, controller errors or overruns;
its minimum data setup is 2,961 modeled DSC cycles. At phase 131,
every original-circuit wrong transition crosses `48` or `2F`, while
the corrected readout recovers all eight source bytes in each selector.
The phase-137 and phase-139 runs validate transfer to new data/carrier
starts, but do **not** test the veto because their states never activate
it. None of these holdouts reaches a previously unseen state relative
to the 20 labeled `81/A1` states.

The [development report](results/joint-mask04-12a-phasebit0-veto.json),
[phase-137 run](results/joint-mask04-12a-phasebit0-veto-phase137-holdout.json),
[phase-139 run](results/joint-mask04-12a-phasebit0-veto-phase139-challenge.json),
[phase-131 1.15× run](results/joint-mask04-12a-phasebit0-veto-phase131-holdout.json),
[phase-131 1.25× run](results/joint-mask04-12a-phasebit0-veto-125gain-holdout.json)
and [audit](results/joint-mask04-12a-phasebit0-veto-holdout-audit.json)
preserve the payloads, PROM trace hashes, capture states, wrong
indices, line/controller bytes, clipping counts and source hashes.
Reproduce from the microcode directory with:

```sh
python3 g2/joint_mask04_12a_phasebit0_veto.py
python3 g2/joint_mask04_12a_phasebit0_veto_phase137_holdout.py
python3 g2/joint_mask04_12a_phasebit0_veto_phase139_challenge.py
python3 g2/joint_mask04_12a_phasebit0_veto_phase131_holdout.py
python3 g2/joint_mask04_12a_phasebit0_veto_125gain_holdout.py
python3 g2/joint_mask04_12a_phasebit0_veto_holdout_audit.py
```

This is a functional external logic hypothesis under assumed capture,
mode, line and serial routes. The extra veto gates have **no assigned
photographed package or traced nets**, so the corrected circuit is not
a physical C3 pass. Next test its 14 unobserved changed-mode predictions
with a deliberately different receive-gain/carrier family and examine
whether photographed spare logic can implement the veto without
conflicting with its existing roles. Keep C3 and G2 active.
