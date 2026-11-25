# A four-row dispatch runs, but its fourth row erases the tested ADC state

The sustained [two-row ADC fixture](RECEIVER-DISPATCH-SOURCE.md) alternates
computed-call indices 0 and 2 at `3EC`. The photographed U24 74LS161 makes
a counter-like index plausible, so this screen tries the complete
`0→1→2→3` sequence under candidate 8X02 TEST flag wiring. The counter
connection, TEST source and timing are **assumptions**, not traced nets.

Using the same real four-PROM and joint upper-slice mapping, a held `09`
ADC code runs for 48,047 instructions under all 16 combinations of previous
or current flag timing, zero/sign/carry/overflow source and polarity.
Five choices sustain all four rows and select 1,500 ADC bytes at `3F8`:

| Flag timing | Select-0 TEST choices that sustain `0→1→2→3` |
| --- | --- |
| Previous ALU flags | inverted overflow |
| Current ALU flags | zero, inverted sign, inverted carry, inverted overflow |

The other 11 choices reach `3F8` at most six times, then leave this loop.
The full-row path uses 32 microinstructions per ADC visit. At an assumed
14.4 MHz microinstruction rate, 47/46 visits per 9,600-Hz reference sample
give a 32-sample, 1,500-visit waveform fixture. Under the previous-overflow
choice, both changing `0,1,3,2` and all-zero dibit patterns complete that
fixture with the **same PC path**: 1,501 visits to the first table row and
1,500 to each other row. All five surviving flag choices also complete
both waveform fixtures.

The ADC affects the third row: `3F8`'s ALU Y and the subsequent `3F9` ROM
address differ on 1,359 of 1,500 visits; `3F9`'s Y differs on 1,336 visits.
After `3FA`, complete RAM-plus-Q state differs on 1,359 visits, including
R11, R12, R13 and Q. After the following `3FE` row, complete RAM-plus-Q
state differs on **zero** of 1,500 visits. Every reached TEST and next-PC
sequence is the same between streams. The fourth row therefore removes
the tested ADC dependence before the next four-row cycle. A separately
clocked latch sampling during the third row could still observe it.

This result permits a photo-compatible full-counter execution, but it does
not establish a receiver: there is no retained multi-sample state or
executed bit decision on this route. The next useful test is a concrete
third-row output latch or another dispatch/condition schedule; missing
continuity does not block either. C3 remains open.

The [machine report](results/receiver-four-row-condition-screen.json)
records all 16 held-byte cases, both reference-waveform digests, each
executed word's output differences and complete row-boundary state counts.
Reproduce with `python3 g2/receiver_four_row_condition_screen.py` from the
microcode directory.
