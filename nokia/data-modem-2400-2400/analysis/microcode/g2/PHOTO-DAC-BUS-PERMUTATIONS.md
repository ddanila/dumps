# One photographed DAC bit does not identify the full bus order

The earlier [six-order decode screen](PHOTO-MAIN-DIBIT-DAC-DECODE.md)
found one simple Q4/Q5 swap with 1 wrong dibit in 104 controller-driven
decisions. A closer look at the [DED 3558 front photo](../../../photos/PXL_20261123_114854803.jpg)
still supports only the candidate **74LS273 Q4→DAC08 B5** segment; the
other seven data traces cannot be assigned confidently from the visible
pad-side tracks. This [exhaustive screen](photo_dac_bus_permutations.py)
therefore holds ordered Am2901 Y→LS273 D wiring fixed and tests **all 7! =
5,040** one-to-one Q→DAC bit assignments that preserve Q4→B5.

Each mapping uses the same four real-controller dibit streams, previously
executed four-visit D127 pulses and independently checked PC129 ROM/Y
recurrence. The selected Q4/Q5-swap code sequence is SHA-256 matched to
the actual PROM traces before the screen. A linearized matched-filter
calculation scores all mappings at the same fixed four-sample timing shift;
five representative mappings are checked against the independent reference
receiver implementation.

| Candidate group | Count | Wrong dibits / 104 | Mean absolute correlation with reference |
| --- | ---: | ---: | ---: |
| All photo-B5-compatible permutations | 5,040 | varies | — |
| Perfect decisions | **12** | **0** | 0.757–0.801 |
| One wrong decision | **172** | **1** | not screened as a group |
| Earlier Q4/Q5-swap choice | 1 of those 172 | 1 | 0.701 |

For example, input-bit→DAC-code-bit order `[4, 0, 6, 1, 3, 2, 5, 7]`
has **zero** wrong decisions and 0.801 mean absolute waveform correlation.
The earlier Q4/Q5 swap is `[0, 1, 2, 4, 3, 5, 6, 7]`. Both satisfy the
photo-suggested input bit 4→DAC code bit 3 (DAC B5). The 12 perfect-decision
orders also beat the earlier swap on the same reference-correlation metric.

This corrects the interpretation of the six-order result: the near-perfect
dibit decoding is strong evidence for **conditional differential phase
information** in the candidate ROM output, but it does **not** identify a
unique DAC bus. Other ordered-Y assumptions, sample timings or analog
shaping would enlarge the candidate space. A second independently constrained
DAC data bit, or an actual latch/line capture, is now needed to choose among
these mappings. None of these permutations proves the pulse gate, latch
clock or physical line output. The [machine report](results/photo-dac-bus-permutations.json)
contains every permutation and its four class error counts, the 12 perfect
orders, correlation values and source hashes.
