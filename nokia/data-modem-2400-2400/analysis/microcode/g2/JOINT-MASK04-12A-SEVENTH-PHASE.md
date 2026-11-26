# One added Y bit restores phase consistency, but the frozen readout remains incomplete

After the [six-bit phase decoder failed](JOINT-MASK04-12A-PHASE-LOGIC-FRESH.md),
I treated its four offset-16/80 runs as development data. The expanded
set has 18 real-PROM receive cases and 1,152 labelled transitions at
the assumed `3F8` Y capture visits 46/93. The six-bit state has 92
four-phase graph conflicts. Both full Y bytes have none. Screening
the ten unused Y bits one at a time found exactly two zero-conflict
seven-bit features:

| Added bit | Observed states | Connected phase components | Prior third-payload checks at offsets 32/96 |
| --- | ---: | --- | --- |
| First-capture Y4 | 25 | 17 + 4 + 4 states | 12/12 cases, all 64 decisions exact |
| Second-capture Y5 | 24 | 13 + 7 + 4 states | 12/12 cases, all 64 decisions exact |

Each component has an arbitrary phase rotation relative to the others.
The frozen decoders therefore abstain on any unseen state or
cross-component transition. The earlier third-payload checks are
reused evidence, not untouched validation for this feature choice.

I then fixed both seven-bit phase maps and offered a fourth eight-byte
payload in each selector mode at new running R1 offsets **48** and
**112**, with the same real-PROM Tx→line→Rx and nominal line gain.
The 64 decisions per run include a 32-dibit payload region.

| Offset | Selector | First-Y4 wrong / unknown | Second-Y5 wrong / unknown | Reference wrong |
| ---: | --- | ---: | ---: | ---: |
| 48 | `40` | 0 / 59 | 3 / 56 | 4 |
| 48 | `60` | 0 / 58 | 6 / 49 | 0 |
| 112 | `40` | 0 / 26 | 3 / 22 | 1 preamble |
| 112 | `60` | 0 / 28 | 5 / 19 | 1 preamble |

First-Y4 makes no *known-component* error, but leaves 26–59 decisions
unknown, including 26–28 of the 32 payload dibits at offset 112.
Second-Y5 makes definite errors and also leaves many unknown. Neither
recovers complete line bytes or a modeled 8251/8031 payload handoff.
The independent reference errors at offset 48 call warn that this
particular candidate line is also imperfect; offset 48 answer and the
payload region at offset 112 provide cleaner controls.

A post-hoc graph audit using the new labels keeps first-Y4 consistent
under a static four-phase model, with 27 states in components of 23
and 4. Second-Y5 becomes inconsistent: 38 conflicts from offset 48,
48 from offset 112, and 86 combined. This rules out second-Y5 as a
complete static readout across the tested starts. The first-Y4 graph
can be extended using these labels, but that extension is a *new fit*,
not a passed holdout; it still needs untouched data and carrier starts.

The [feature screen](results/joint-mask04-12a-seventh-phase-bit.json),
[offset-48](results/joint-mask04-12a-seventh-phase-fresh-48.json) and
[offset-112](results/joint-mask04-12a-seventh-phase-fresh-112.json)
real-PROM reports, and [post-hoc audit](results/joint-mask04-12a-seventh-phase-audit.json)
contain state phases, trace digests, decisions, controller readout and
source hashes. Reproduce with:

```sh
python3 g2/joint_mask04_12a_seventh_phase_bit.py
python3 g2/joint_mask04_12a_seventh_phase_fresh.py
python3 g2/joint_mask04_12a_seventh_phase_audit.py
```

The photographed ADC, latch and receive logic still do not identify
the capture edges or this phase map. C3/G2 remain open. A next bounded
test can use first-Y4 with the new cases explicitly included in
development, freeze its 27-state rule, and challenge fresh payloads
and carrier starts. In parallel, test a photo-compatible third capture
or carrier-history signal so the explanation can predict new states
without fitting their payload labels.
