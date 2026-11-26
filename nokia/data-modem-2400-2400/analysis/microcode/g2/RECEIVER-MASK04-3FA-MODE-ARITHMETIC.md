# Held `3EB` mode bytes do not make `3FA` consume old R13

This [real-PROM audit](receiver_mask04_3fa_mode_arithmetic.py) executes
two independent legal receive streams under three labeled candidate
controller-frame bytes at `3EB`: held `01`, `81`, and `A1`. The `01`
trace and ADC hashes match earlier carrier runs. All six 192,047-word
runs sustain 6,000 ADC visits, giving **36,000 checked `3FA` words**.
The `3EB` input route is a photo-compatible assumption, not a traced net.

At every checked `3FA`, the mapped instructions are low/high `55/C5`
with A=R10, B=R13 and D=`01`. The low slice computes
`lo = (1 + ~R10lo + carry_in) & 0xF`; its carry feeds the high slice,
which computes `hi = (R10hi + low_carry) & 0xF`. Executed Y is
`(hi << 4) | lo`. The high result replaces R13's high nibble while its
low nibble and Q stay unchanged. The checker verifies the instructions,
addresses, F/Y, Q and all RAM destinations on every word. **Old R13 is
the destination's previous value, not an ALU operand** in this mapping.

| Held `3EB` byte | Matched ADC/phase groups with varying pre-R13 | Groups with varying `3FA` Y, post-R13 or Q |
| --- | ---: | ---: |
| `01` | 8/21 | 0 |
| `81` | 6/21 | 0 |
| `A1` | 4/21 | 0 |

Relative to the same-input `01` run, `81` changes pre-R13 on 10,827 of
12,000 visits but changes neither Y, post-R13 nor Q. `A1` changes
pre-R13 on 11,107 visits and changes Y/post-R13 on all 12,000 visits;
the equation attributes that output change to its R10 operand, and
matched exact-ADC/phase groups still have no Y or Q variation within
the mode. These held-byte cases therefore do not expose the transient
history value as a recovered bit. They do show an executed mode-byte
effect on the arithmetic under the stated wiring hypothesis.

Next try a distinct, photo-compatible return or mux timing that puts a
stored value on an A or D input before it is overwritten, and compare
the same own/remote/mixed controls at a real output candidate. This
negative result does not rule out other board modes or circuits. C3/C4
and G2 remain open without waiting for new pin continuity.

The [machine report](results/receiver-mask04-3fa-mode-arithmetic.json)
contains trace hashes, equation counts, matched group counts and mode
contrasts. Reproduce with
`python3 g2/receiver_mask04_3fa_mode_arithmetic.py`.
