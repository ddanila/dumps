# The eight-state receive lookup is tied to its ADC input level

The [row-pair phase-code result](RECEIVER-MASK04-ROWPAIR-PHASE-CODE.md)
recovered all 96 independent dibits at one ideal PCM amplitude using a
frozen eight-state lookup. This [level check](receiver_mask04_rowpair_level_check.py)
keeps that exact lookup, capture phase, mask-`04` mapping, four-row schedule
and reference dibits. It changes only the signed PCM before complementary
ADC encoding, then runs six new **192,047-instruction real-PROM** receive
traces. A periodic and a nonperiodic stream are used for each level.
The independent reference receiver still recovers every changed waveform's
dibits, so a failure here is specific to this DSC lookup fixture.

| PCM change | Recognized transitions | Wrong among recognized | Unknown |
| --- | ---: | ---: | ---: |
| Gain 0.75, no bias | 2/24 | 2 | 22 |
| Gain 1.25, no bias | 21/24 | 0 | 3 |
| Gain 1.0, bias +16 | 10/24 | 4 | 14 |

The 0.75-gain case clips no PCM samples, yet the frozen codebook recognizes
almost none of its phase-state pairs. Gain 1.25 clips 78 samples per stream;
the positive-bias cases clip 35–37. Those latter cases are useful stress
tests, not clean independent measurements of gain or bias tolerance.
Rows 1 and 2 of the proposed `3ED` latch remain zero in all six traces;
the two varying rows now visit 34–43 distinct byte pairs over the full
trace. The [machine report](results/receiver-mask04-rowpair-level-check.json)
records per-stream recognized/error/unknown counts, clipping, trace and
capture hashes, and source hashes.

The prior phase-code finding remains a valid conditional witness at its
declared input level, but a fixed eight-state lookup is **not** a general
receiver for these still-decodable waveforms. Next test whether an executed
threshold, gain-control or stateful decision consumes the row pair, or
whether a separately labelled normalized lookup generalizes. No USART-01
RxD route is identified, so C3 remains open. Reproduce from the microcode
directory with `python3 g2/receiver_mask04_rowpair_level_check.py`.
The [row-3 parity-gate follow-up](RECEIVER-MASK04-ROW3-PARITY-GATE.md)
finds a smaller readout that does generalize across these levels for one
dibit parity bit; it does not yet supply both received bits or RxD wiring.
