# ADC sample margin as a receive capture selector

The [executed gap audit](RECEIVER-MASK04-HOLDOUT-GAP-AUDIT.md) showed that
the two unresolved +7 Hz dibits occurred when an early ADC sample was near
the fixture's zero midpoint. It suggested a concrete, answer-independent
sampling hypothesis: prefer samples farther from that midpoint. This
[experiment](receiver_mask04_adc_margin_selector.py) freezes the existing
two decision tables and tests three visit pairs, 46/93, 47/94 and 94/141.
For each differential decision, it ranks those pairs by the **smallest
absolute distance from ADC byte 127** among the pair's two samples in both
the current and previous symbols. It uses the highest-ranked pair with a
known frozen-table decision; ties retain the listed pair order. The rule
does not inspect reference dibits or use symbol-specific exceptions.

Four new 96-symbol real-PROM streams use seed `E35A`, carrier offsets ±7 Hz
and initial phases 75°/165°. Each stream has 32 `11` preamble and 64 data
symbols, executes 1,152,047 words and accepts 36,000 complementary ADC
visits. The independent reference receiver decodes every PCM input before
the PROM replay. The same executed traces are scored with the earlier
conservative 46/93 + 47/94 union as a control.

| Offset, phase | Two-pair control: wrong / unknown / 95 | ADC-margin selector: wrong / unknown / 95 |
| --- | ---: | ---: |
| −7 Hz, 75° | 0 / 0 | 0 / 0 |
| −7 Hz, 165° | 0 / 1 | 0 / 0 |
| +7 Hz, 75° | 0 / 1 | 0 / 0 |
| +7 Hz, 165° | 0 / 0 | 0 / 0 |

The frozen margin rule gives **0 wrong and 0 unknown among 380 measurable
dibits**, including all 256 data dibits. The two-pair control leaves two
data dibits unknown. The selector actually uses all three pairs in each
case; the later 94/141 pair is selected 15–29 times per stream, so the
result exercises more than a fixed early sampling edge.

This is evidence that the executed PROM receive state contains enough
information for a plausible signal-strength-guided readout on these
fixtures. It is **not** evidence that the Nokia board implements this
selector: ADC reference range and polarity, symbol-relative clocks,
three capture latches, comparison logic, decision tables and
RxD/RxC/SYNDET connections remain hypotheses. The rule was inspired by
two inspected gaps; this seed is a fresh challenge, but other data,
intermediate offsets, noise and acquisition behavior still need testing.
C3 stays open. Next constrain a selector/latch path from the available
photos and executed clock edges, then test the same frozen rule on another
independent stream and the controller's real receive timing.

The [machine report](results/receiver-mask04-adc-margin-selector.json)
records every case's trace and ADC hashes, pair scores, selected-pair
counts and source hashes. Reproduce from the microcode directory with
`python3 g2/receiver_mask04_adc_margin_selector.py`.
