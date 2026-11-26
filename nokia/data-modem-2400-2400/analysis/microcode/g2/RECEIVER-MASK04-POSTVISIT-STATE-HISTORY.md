# Matched ADC visits retain a transient R13 difference, then erase it at `3FA`

This [instrumented real-PROM replay](receiver_mask04_postvisit_state_history.py)
runs two legal rotated-carrier streams through the mask-04 receiver loop.
Their 192,047-word trace and held-ADC hashes match the previously saved
independent-carrier runs. At the first visit of each held ADC sample, it
captures pre/post Q and all sixteen Am2901 RAM registers at `3F9`, `3FA`
and `3FE`, with the selected ROM address and Y output.

The audit matches samples by **the same exact ADC byte and the same
0–7 position within a symbol**, then keeps groups with at least two
different preceding ADC bytes. There are 21 such groups. In eight,
pre-`3F9` R12 and R13 differ, and only R13 still differs after `3F9`.
`3F9` executes `15/C5` in this mask-04 mapping. Its selected ROM
address, Y and post-Q agree within all 21 groups.

At `3FA`, the same eight groups enter with different R13 values, but
the executed `55/C5` instruction writes the **same post-R13** value.
Post-`3FA` Q, all RAM registers and Y then agree within every matched
group; they still agree after `3FE` (`D4/C5`). A concrete witness holds
current ADC byte `D9` at symbol sample position zero: differing preceding
bytes `F2` and `4C` leave pre-`3FA` R13 at `50` and `40`, but both yield
post-`3FA` R13=`20`. Both cases select `3F9` ROM address `1DF`, produce
`3F9` Y=`31`, and retain Q=`81`.

The difference is real internal history under this assumed input route,
but it is **not a recovered dibit** or an externally established output:
the tested Y/Q values do not expose it, and the direct-mode loop erases
it at `3FA`. A fixed `3F9` Y latch cannot capture this R13 difference.
Next test a photo-compatible mode or RAM-return route that makes this
state a consumed operand or later Y/Q output before overwrite, with
matched-input controls. C3/G2 remain open; missing continuity does not
block that explicit experiment.

The [machine report](results/receiver-mask04-postvisit-state-history.json)
records group counts, instruction pairs and matched witnesses. Reproduce
with `python3 g2/receiver_mask04_postvisit_state_history.py`.
