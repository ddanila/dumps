# Boundary impulses separate two candidate receive capture phases

The [long zero-run handoff](RECEIVER-MASK04-DUAL-ZERO-HANDOFF.md) succeeds
whether the frozen receive readout uses the candidate latch at row-3 `3ED`
after ADC visits 47/94 or the same latch at row-0 `3ED` just before those
visits. The latter holds the preceding visit's Y5–Y7. This experiment
tests whether those are genuinely distinct executed capture phases.

A new 75° stream contains eight `11` preamble symbols, 16 seed-`AC17`
data dibits and eight trailing zero dibits. For each of three fixtures,
the joint mask-`04` mapping executes 384,047 real-PROM instructions and
12,000 candidate ADC visits. The raw-PROM clock produces 12,001 edges:
one startup edge and one per `3F8→3F9` receive visit. At each selected
visit, the row-3 latch value equals the executed `3F8` Y5–Y7. The
pre-capture value comes from row 0 before that visit's edge.

| ADC fixture | Row-3 current-visit readout | Row-0 preceding-visit readout |
| --- | ---: | ---: |
| Natural PCM | 0 wrong, 0 unknown / 31 | 0 wrong, 0 unknown / 31 |
| XOR ADC bit 7 for one visit at 47/94 | 0 wrong, **13 unknown** / 31 | 0 wrong, 0 unknown / 31 |
| XOR ADC bit 7 for one visit at 46/93 | 0 wrong, 0 unknown / 31 | 0 wrong, **11 unknown** / 31 |

The impulses are deliberately artificial one-visit ADC perturbations;
they are not measured line events. No held-out reference answer is used
to fill an unknown decision. The reciprocal result shows that the two
readouts depend on different executed samples even though both decode
the natural fixture. It does **not** decide which phase the Nokia board
uses, and the impulse result is not a robustness claim for the modem.
The candidate clock gate, symbol-visit counter, capture registers,
transition readout and USART connection remain hypotheses. A board-compatible
symbol clock or another natural stimulus that distinguishes the two
phases is needed to choose one before treating the readout as C3 evidence.

The [script](receiver_mask04_capture_phase_boundary.py) and
[machine report](results/receiver-mask04-capture-phase-boundary.json)
retain the trace digests, impulse values, decision lists and source hashes.
Reproduce from the microcode directory with
`python3 g2/receiver_mask04_capture_phase_boundary.py`.
