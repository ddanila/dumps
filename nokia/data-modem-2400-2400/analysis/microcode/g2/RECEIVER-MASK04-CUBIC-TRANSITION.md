# Cubic constraints extend the executed two-visit receiver readout

The [four-bit transition test](RECEIVER-MASK04-TWO-VISIT-TRANSITIONS.md)
uses `3F8` Y6/Y7 at ADC visits 47 and 94 to form a four-bit state for
each symbol. Its 86 observed previous/current-state keys have consistent
dibit labels, but five keys are absent from the development traces and
remain unknown on the independent 13-angle PROM run. This
[follow-up](receiver_mask04_cubic_transition.py) asks which unseen labels
are *forced* by a low-degree Boolean relation, without reading their
reference dibits during fitting.

For each two-bit output separately, the script evaluates all monomials of
degree at most two or three in the eight previous/current-state bits and
solves the resulting equations over GF(2). No degree-two rule fits all 86
development keys: the 37-column system has full rank and 35 contradictory
rows. Degree three has 93 columns, rank 76 and no contradiction. The fit is
non-unique. An unseen key receives a prediction only if its feature vector
lies in the span of the development vectors, so **every** fitting cubic
rule gives the same two-bit label. Fourteen of the 170 unseen keys meet
that condition; the other 156 remain unknown.

| Independent run | Frozen 86-key lookup | Lookup plus forced cubic labels |
| --- | ---: | ---: |
| Saved new seed, 13 angles, 611 decisions | 0 errors, 5 unknown | **0 errors, 1 unknown** |
| New `C4E1` seed, 0°/75°/165°, 141 decisions | 0 errors, 3 unknown | **0 errors, 0 unknown** |

In the saved 13-angle run, the previously unknown `D9`, `E8`, `7B` and
`FC` keys are forced to dibits 3, 1, 3 and 1, matching the held-out
reference. Key `3C` remains unconstrained; its observed dibit 0 is
recorded for evaluation only. The new-seed run executes three fresh
576,047-instruction real-PROM streams with one shared random data sequence.
It covers a grid angle, an intermediate angle and a high intermediate
angle. The report retains trace and ADC hashes, the exact input sequence,
per-angle scores and source hashes.

This is a stronger conditional receive readout, **not** a recovered Nokia
Boolean circuit or a C3 pass. The cubic family contains many possible
rules, the unresolved `3C` decision shows that the current development set
does not determine every observed transition, and no physical two-visit latch,
symbol memory, RxD/RxC or external SYNDET path has been established. Next
test another executed bit/visit or retained phase state against `3C` and
new angles, then carry a complete frozen decision stream through the
paced USART/controller handoff. Unknown wiring remains an experiment
assumption, not a goal blocker.

The [machine report](results/receiver-mask04-cubic-transition.json) is
reproduced from the microcode directory with
`python3 g2/receiver_mask04_cubic_transition.py`.
