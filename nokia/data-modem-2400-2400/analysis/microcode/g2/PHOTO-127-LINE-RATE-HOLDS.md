# The direct serial-bit phase route exits before a real-rate stream

The [joined frame/line run](PHOTO-127-FRAME-LINE-JOINT.md) used short
diagnostic bit holds. The [timed replay](photo_127_line_rate_holds.py) keeps
the same real 8031 frame lane and USART-01 bytes but derives each bit hold
from the board's 14.4 MHz oscillator, a hypothesized `k=1…4` oscillator
periods per microinstruction, the executed four-word `12C–12F` loop, and
2,400 data bits/s. Thus each bit occupies `1500/k` visits to D12C.
The oscillator-to-microinstruction divider and both D-input routes are
still hypotheses.

| Clock divisor `k` | D12C visits/bit | Selector `00`: D12C reads before wait | Selector `20`: D12C reads before wait |
| ---: | ---: | ---: | ---: |
| 1 | 1,500 | 1,755 | 255 |
| 2 | 750 | 1,005 | 255 |
| 3 | 500 | 755 | 255 |
| 4 | 375 | 630 | 255 |

All 16 real-PROM runs execute 9,000 microinstructions cleanly. In the two
`47` frame classes, every reached D12C input and upper-bank PC12E ROM read
matches the offered bit and cumulative phase recurrence. Selector `00`
begins with bit 0: its entire first bit holds the ROM address at `101`.
The next bit is 1, and the loop reaches phase zero on its 255th visit,
exiting to the `084` wait **during the second bit**. Selector `20` begins
with bit 1 and exits on its 255th visit, **during the first bit**. The
`42` frame classes (`40`/`60`) remain in the first loop and select no D12C
input. No run reaches candidate output words `392` or `39E`.

This excludes **unmodified USART serial bits directly driving D12C** as a
sustained transmitter under these four clock/divider hypotheses. A held
zero does not advance this phase walk, and a held one makes it leave before
one bit interval ends. The short-hold joined result remains a valid
conditional control-flow witness, but it does not scale to the proposed
physical bit rate. The [report](results/photo-127-line-rate-holds.json)
retains every hold, selected-read count, first-bit ROM addresses, wait
cycle and trace digest. A decoded or biased D12C input, a different clock,
or another stateful ROM/output path remains an executable hypothesis.
