# A direct third-row output bit does not recover the dibits

The [four-row condition screen](RECEIVER-FOUR-ROW-CONDITION.md) found that
reference ADC samples change Y, flags and RAM/Q during `3F8–3FA`, but the
next row removes the retained difference. A separately clocked latch could
sample the brief ADC-sensitive window. This screen tests the simplest such
route: one Am2901 Y-bus bit or ALU flag sampled at a fixed phase of each
symbol, with either polarity and optional XOR against the previous symbol.
The latch clock and output wiring remain hypotheses.

Seven independent reference streams use three training and four holdout
sequences. Each executes 192,047 real-PROM microinstructions and selects
6,000 complementary ADC bytes at `3F8` under the same counter-like
`0→1→2→3` dispatch and inverted previous-overflow loop test. The ADC hold
is 47/46 loop visits per 9,600-Hz reference sample, giving 375 visits per
1,200-baud symbol. Each stream takes all four table rows and the reference
receiver recovers its supplied dibits. The screen checks Y bits 0–7 and
sign, zero, carry and overflow at each of `3F8`, `3F9` and `3FA`, all 375
sample phases, symbol lags −2…+2, and both bit polarities.

| Readout | Dibit bit | Exact training fits | Best training / holdout errors |
| --- | ---: | ---: | ---: |
| Direct pin bit | 0 | 0 | 10/36 · 7/48 |
| Direct pin bit | 1 | 0 | 11/36 · 6/48 |
| Pin bit XOR previous symbol | 0 | 0 | 9/36 · 7/48 |
| Pin bit XOR previous symbol | 1 | 0 | 11/36 · 5/48 |

Thus a single fixed-phase latch bit from these reached output pins is not
the received dibit in this fixture. This does **not** rule out a multi-bit
decision circuit, a stateful output path, another clock/phase model, or a
different dispatch/condition/input mapping. No modeled bit has been traced
to USART 01 RxD. Keep C3 open and test another photo-compatible route rather
than waiting for physical continuity.

The [machine report](results/receiver-four-row-latch-screen.json) includes
all stream digests, the best candidates, exact-fit counts, fixtures and
source hashes. Reproduce with `python3 g2/receiver_four_row_latch_screen.py`
from the microcode directory.
