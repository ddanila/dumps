# A half-quadrant phase offset exposes a missing receive-state normalization

The [running-phase challenge](JOINT-MASK04-12A-RUNNING-PHASE.md) found
that adding `20` to the executed R1 accumulator at the first data
sample caused one or three external reference-decoder errors. To test
whether the abrupt data-boundary intervention caused them, this replay
moves the same one-time `20` offset to the start of the muted interval
(`127` visit 96,001), or four output samples before data (`127` visit
118,501). The real-PROM q3/mask-04 transmitter, fresh payloads, bus-0
DAC candidate, Q=0.5 filter, +6 alignment and fixed gain are unchanged.

| Selector | Step at data onset | Step at mute start | Step four samples before data |
| --- | --- | --- | --- |
| `40` | reference error at decision 40 | same | same |
| `60` | reference errors at 40–42 | same | same |

Thus merely moving the intervention away from the data boundary does
not remove those errors. In the executed receiver replay at mute start,
the frozen seven-state rule encounters states `2,6,9,D`; `2` is unknown,
and the old labels for the others are no longer all suitable. It makes
9 wrong and 9 unknown data decisions in call mode, and 10 wrong and 12
unknown in answer mode. Neither stream reaches a complete line-byte or
controller handoff under that frozen rule. The quarter-turn success in
the earlier challenge therefore does not establish arbitrary start-
phase robustness.

There is still a compact phase structure. Enumerating all 64
four-state labelings with state `2` fixed to phase 0 (the global
rotation is arbitrary) gives **exactly one** labeling that decodes the
call stream: `2→0, 6→3, 9→1, D→2`. The same rule, with no answer-side
fitting, decodes all 64 answer dibits. Both streams recover the exact
eight offered line bytes; with aligned assumed SYNDET, the modeled
8251/unchanged 8031 consumes eight bytes without errors or overruns
and descrambles `D3 26 91 4E B8 07 5C EA` and
`6A D5 02 B9 40 EF 73 1C`, respectively.

This call-trained relabeling is **not** evidence that the physical
receiver can choose it. The missing mechanism may involve carrier
phase tracking, gain/threshold changes, or a different photo-compatible
capture/logic path. The result narrows the next C3 test: identify or
construct a circuit using the photographed ADC and available latch/
clock resources that selects a consistent quadrant state across
different carrier starts, then freeze and challenge it on new data and
levels. C2/C3 and G2 remain open; missing continuity is a testable
assumption, not a goal blocker.

The [timing transmit report](results/joint-mask04-12a-phase-timing.json),
[frozen receive report](results/joint-mask04-12a-phase-timing-rx.json)
and [call-fit/answer-holdout report](results/joint-mask04-12a-phase-timing-map.json)
record trace digests, states, decisions and controller handoffs. Reproduce
from the microcode directory with:

```sh
python3 g2/joint_mask04_12a_phase_timing.py
python3 g2/joint_mask04_12a_phase_timing_rx.py
python3 g2/joint_mask04_12a_phase_timing_map.py
```
