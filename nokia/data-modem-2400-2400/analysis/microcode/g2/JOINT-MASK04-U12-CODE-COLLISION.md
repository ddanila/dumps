# The candidate U12 row pair loses a real DSC input distinction

The [controlled replay](joint_mask04_u12_code_collision.py) gives the same
real-PROM mask04 receiver fixture two ADC streams. Both are `7F` except for
sample 25, held for 47 receive visits: one stream uses `1F`, the other `6F`.
Each stream executes 96,047 microinstructions. The trace digests differ,
confirming that the change reached the DSC model.

At each of the 47 changed-input visits, the executed Y bytes at `3F8`,
`3F9` and `3FA` differ. Yet the `3ED` Y capture, post-visit Q and all
sixteen Am2901 RAM bytes are identical at every one of the 3,000 visits.
The assumed U12 row-0 low-nibble latch and live row-3 low-three-bit input
are also identical for all 3,000 visits. Clocking that latch on every raw
`3ED` edge gives the same result. This is a whole-stream collision for the
tested U12 readout, not just a collision at the prior phase-47 sample.

Consequently, a causal tracker fed **only** this proposed U12 row pair
cannot distinguish these two ADC streams; more history of the same pair
does not restore the lost sample. The experiment uses artificial one-sample
pulses, so it does not prove that legal modem dibits are indistinguishable,
nor does it exclude other DSC outputs or analog history. It does show why
the U12-only tracker is a weak next C3 route despite the demonstrated
previous/current latch timing. The board clock, Y-to-U12 pins and row-3
consumer remain photo-compatible assumptions.

Next compare a candidate `3F9`/`3FA` output latch against the same matched
input pair and against legal rotated-carrier streams, then ask whether its
information survives into a symbol-time decision and controller/USART RxD.
The direct `3F8` Y byte contains the raw ADC high nibble, so a decoder
driven solely by it would demonstrate external demodulation of ADC data,
not a DSC microprogram receive decision. C3 stays open; the uncertain wire
is a testable hypothesis rather than a goal blocker.

The [machine report](results/joint-mask04-u12-code-collision.json) contains
both input and trace hashes and difference counts for every captured
channel. Reproduce from this directory with
`python3 g2/joint_mask04_u12_code_collision.py`.
