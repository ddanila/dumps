# The four-row ADC window carries signal, but no generalizing byte readout

The [four-row condition screen](RECEIVER-FOUR-ROW-CONDITION.md) found a
photo-compatible `0→1→2→3` dispatch that sustains reference ADC input. Its
third row changes Y, Q and RAM before the fourth row erases the tested
state difference. The [direct-bit latch screen](RECEIVER-FOUR-ROW-LATCH-SCREEN.md)
found no single fixed-phase output bit that decodes the dibits. This test
asks whether a byte captured in that brief third-row window could instead
act as a received sample for a fixed differential decoder.

Eleven independent 192,047-instruction real-PROM runs use the same joint
upper-source mask-08 mapping, assumed inverted previous-overflow TEST,
four-row dispatch and complementary ADC input. Every run selects 6,000
ADC bytes at `3F8` and completes the table schedule. The ADC holds each
reference sample for 47 or 46 visits. The first seven streams are divided
into three training and four holdout cases; four more random streams are
fresh validation.

The screen samples Y at `3F8–3FA`, Q and R10–R13 at the start, center or
end of each ADC hold, with a ±2-visit offset. Each byte is interpreted as
offset binary or signed two's complement. A fixed *external* reference
receiver then tries five symbol lags. Of 1,200 readouts, 20 fit all 36
training dibits, but **none** fits both training and holdout. The best
training readout is offset-binary Y at `3F8`, two visits before the ADC hold
ends, at zero symbol lag:

| Check | Dibit errors |
| --- | ---: |
| Training | 0/36 |
| Holdout | 7/48 |
| Four fresh streams | 1/12, 4/12, 2/12, 5/12; 12/48 total |
| Reference PCM on four fresh streams | 0/48 |

This is evidence that the third-row output still reflects the input
waveform, but the tested fixed byte readout does not recover an independent
dibit stream. More importantly, the decoder here is a diagnostic outside
the DSC; no executed microcode bit decision or route to USART 01 RxD has
been found. The assumed dispatch, TEST source, ADC bus, sample clock and
latch phase also remain untraced. C3 stays open. Test an instruction-driven
stateful decision or a different photo-compatible latch/dispatch route;
missing continuity does not block that work.

The [machine report](results/receiver-four-row-sampled-state-dpsk.json)
contains the selection counts, full-state trace digests, fixture, train,
holdout and validation scores, and source hashes. Reproduce with
`python3 g2/receiver_four_row_sampled_state_dpsk.py` from the microcode
directory.
