# A fixed phase-47 Boolean readout recovers both reference dibit bits

The [row-3 gate](RECEIVER-MASK04-ROW3-PARITY-GATE.md) recovered one
combination of dibit bits across input levels. The [phase-47 codebook
screen](receiver_mask04_phase47_joint_codebook.py) found a stronger capture
site: one phase-label graph fit all 72 training transitions at 0.75 gain,
1.25 gain and +16 PCM bias. Frozen before its random holdout, that graph
made **0 errors on 87 recognized transitions**, leaving nine unknown.
Inspecting those unknown byte pairs yielded this fixed Boolean rule for
the two `3ED` Y bytes captured on rows 0 and 3 of ADC visit 47 within
each 1,200-baud symbol:

```text
r0 = row-0 Y; r3 = row-3 Y
phase.low  = r0.b0 OR r0.b2
phase.high = r0.b3
          OR (r0.b2 AND (NOT r0.b0 OR r3.b2))
          OR (r0.b1 AND NOT r0.b0 AND r3.b0 AND (r3.b1 OR r3.b2))
phase = phase.low + 2 * phase.high
step  = (phase[current] - phase[previous] - 2) mod 4
dibit = (00, 01, 11, 10)[step]
```

The subtraction of two quadrants removes the reference 1,800 Hz carrier's
180° advance per 1,200-baud symbol. The [logic replay](receiver_mask04_phase47_logic.py)
first checks the rule on the **development data** used to derive it: six
changed-level traces plus the eight inspected codebook holdouts, 168
transitions in all. It then freezes the rule and runs two new random
streams at each of four levels. Each new case executes **192,047 real-PROM
microinstructions**, verifies the receive path and proposed PROM latch
count, and checks the independent reference modem still decodes the
changed waveform.

| Input level | Fresh transitions | Dibit errors |
| --- | ---: | ---: |
| Nominal gain, no bias | 24 | 0 |
| Gain 0.75, no bias | 24 | 0 |
| Gain 1.25, no bias | 24 | 0 |
| Nominal gain, PCM bias +16 | 24 | 0 |
| **Fresh total** | **96** | **0** |

The rule also makes 0/168 errors on its development traces. That number
is descriptive, **not independent validation**: the formula was adjusted
after inspecting the earlier holdouts. The two seeds in the table were
new and were not used to select the formula. Unlike the earlier
eight-state phase-0 lookup, this fixed rule supplies a dibit decision for
every tested changed-level symbol. The [machine report](results/receiver-mask04-phase47-logic.json)
contains the eight fresh trace and capture hashes, complete symbol pairs,
decoded dibits, fixture values and source hashes. The preceding
[codebook report](results/receiver-mask04-phase47-joint-codebook.json)
retains the frozen 87/96 validation and nine unknowns.

This is a **conditional receiver explanation**, not a C3 pass. The real
PROMs compute the two changing Y bytes under the labelled mask-`04`,
complementary-ADC, four-row fixture. The Boolean readout, previous-symbol
phase storage, `3ED` capture circuit, symbol clock and USART-01 RxD wire
are external hypotheses. The tested reference streams also use one
carrier phase and limited gain/bias values. Next, model a photo-compatible
row-0 latch and row-3 consumer at the executed PROM edges, then test its
two output bits at USART timing. The shifted-carrier test below checks
the separate phase-tolerance question; do not mark G2 blocked on the
untraced wires.

Reproduce from the microcode directory with
`python3 g2/receiver_mask04_phase47_joint_codebook.py` and
`python3 g2/receiver_mask04_phase47_logic.py`.
The [carrier-rotation follow-up](RECEIVER-MASK04-CARRIER-PHASE-SCREEN.md)
finds that 45° and 135° rotated, still-decodable inputs defeat this fixed
readout even after screening every ADC capture visit. Its zero-error
multi-level result is specific to the original carrier-phase grid.
