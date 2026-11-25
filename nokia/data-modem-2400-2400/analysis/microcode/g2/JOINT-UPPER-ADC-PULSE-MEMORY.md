# One ADC pulse exposes a five-visit state-memory phase

The joint TX/ADC map's `D3F8–3FA` loop changes state and ROM addresses when
the ADC high nibble changes, but the [same-map decision screens](JOINT-UPPER-RECEIVE-DECISION.md)
found no direct dibit bit. The [pulse experiment](joint_upper_adc_pulse_memory.py)
asks a narrower question: does one changed ADC byte survive after all later
input bytes return to the same value?

It runs the real control PROMs and Am27S31 table for 6,000 `D3F8` visits
with Q=5 and a held baseline byte `09`. Ten paired runs replace **one**
visit with `59`, at visits 10–14 and again at 100–104. The PC path and
all later offered bytes match the control. The changed byte is selected by
the ALU at `D3F8`; the comparison follows Q, all RAM bytes, Y at `3FA`,
and the next `3F9` ROM address after every visit.

| Pulse visit modulo 5 | Later visits with changed state and `3F9` address | Last changed visit |
| ---: | ---: | ---: |
| 0 | All remaining visits | 5,999 |
| 1 | All remaining visits | 5,999 |
| 2 | 0 | Pulse visit only |
| 3 | 2 | Pulse visit + 2 |
| 4 | All remaining visits | 5,999 |

The pattern repeats for the pulse window shifted by 90 visits. In the
persistent classes, Q and RAM 10–13 account for the continuing state
differences; the `3F9` ROM-address difference settles into a five-visit
cycle rather than one fixed offset. The [saved report](results/joint-upper-adc-pulse-memory.json)
gives every visit count, register-difference count, late address-delta
histogram and trace digest.

This is a **conditional memory and timing result**, not a recovered symbol.
The diagnostic one-visit pulse is shorter than the separately assumed
188/187-visit ADC sample holds, which would encounter every phase. The
ADC conversion clock, U8 instruction wiring and USART output remain
untraced. A next receiver readout should respect this five-visit state
cycle and test several state samples or a separately clocked latch across
nonperiodic dibit streams; a single fixed byte at a symbol phase is
insufficient in the screens already run.

Reproduce with:

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/joint_upper_adc_pulse_memory.py
```
