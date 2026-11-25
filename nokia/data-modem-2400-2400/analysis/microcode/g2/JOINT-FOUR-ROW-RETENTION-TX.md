# One fixed candidate map retains receive state and keeps the full transmit waveform

The earlier [joint upper-source screen](JOINT-UPPER-SOURCE.md) found five
nearby photo-compatible field maps that sustain a short ADC run and a held
transmit phase loop. Its selected lower-field mask `08` later passed the
full controller-driven transmitter replay, but the [four-row condition
screen](RECEIVER-FOUR-ROW-CONDITION.md) showed that mask `08` erases the
tested ADC state after the fourth row. This experiment runs all five maps
through the complete receive table and then runs the sole retention
survivor through both full transmit controller modes.

The maps share the same hypothesized inverted U17 D5 upper I0/I7 source,
split-slice links and ADC route. Mask `04` selects the q3 source for lower
I1; mask `08` instead selects it for lower I2. These source assignments
and the TEST/dispatch wiring are **not** traced board nets. Each of five
maps executes 48,047 real-PROM instructions for each of two 32-sample
complementary ADC waveforms, with counter-like `0→1→2→3` dispatch and
inverted previous-overflow TEST. Every case selects 1,500 ADC bytes at
`3F8` and follows the same PC path between the two waveforms.

| Lower-field mask | Different RAM/Q states after ADC row `3FA` | Different RAM/Q states after fourth row `3FE` |
| ---: | ---: | ---: |
| `04` | 1,312/1,500 | **1,312/1,500** |
| `06` | 1,312/1,500 | 0/1,500 |
| `08` | 1,359/1,500 | 0/1,500 |
| `0A` | 1,359/1,500 | 0/1,500 |
| `0E` | 1,312/1,500 | 0/1,500 |

For mask `04`, R1 differs after `3FE` on 1,312 visits, R12 on 563 and Q
on 1,171. Four additional independent nonperiodic 128-sample streams
each complete 6,000 four-row ADC visits under mask `04`, with the same PC
path as an all-zero-dibit control. Their complete RAM/Q state after `3FE`
differs from that control on **3,701–4,780 of 6,000 visits**. This is
retained input-dependent microprogram state across the full table cycle,
not merely a transient third-row result.

The same fixed mask `04` then runs the uninterrupted, controller-derived
A1 tone → A2 interval → A3 sync-fill reversals → A4 data stimulus for
both call (`40`) and answer (`60`) selectors. Each completes 1,248,256
microinstructions, reaches `129` 312,054 times and supplies 832 candidate
samples when Y is taken every 375 visits. All six photo-compatible DAC bus
orders tested with the same assumed A2 gate and fixed bandpass have a
2,100 Hz late A1 raw-code peak and **0/62 filtered A3/A4 differential
decision errors** in each selector. Thus the receive retention is gained
without losing the tested full transmitter behavior under this field map.

The receive comparison also records 234 changed TEST values at `3EA`
under mask `04`, but no changed TEST at looping `3ED` and no changed PC.
The executed `3EA` command is PLP (`5`), which does not branch on TEST in
the sequencer model; those changed levels are not a receive decision.
It has not recovered a bit or an echo-cancelled residual. The DAC clock,
bus and analog line path remain candidates, so C2 is still conditional;
the ADC route, TEST wiring, decision readout and USART RxD route keep C3
open. Mask `04` is the current stronger **joint hypothesis**, not a
verified Nokia field map. A direct screen of its surviving R1/R12/Q bits
is in [the retained-bit follow-up](RECEIVER-MASK04-RETAINED-BIT.md).

The [machine report](results/joint-four-row-retention-tx.json) saves all
receive contrasts, four fresh stream digests, both full transmitter traces,
bus/decoder metrics and source hashes. Reproduce with
`python3 g2/joint_four_row_retention_tx.py` from the microcode directory.
