# The best data buses also carry the candidate A1 tone change

The [exhaustive bus screen](PHOTO-DAC-BUS-PERMUTATIONS.md) left 12
photo-B5-compatible DAC orders with zero errors in 104 real-controller
dibit decisions. This [joint screen](photo_dac_joint_data_tone.py) holds
each order fixed and checks the same bus against the independently executed
[A1 mode-change run](PHOTO-A1-DYNAMIC-MODE-REPLAY.md). The controller's
third frame byte changes `A1→81` in a held-A1 fixture; the previously
proposed small logic decode changes D127 `B0→88`. The DSC PROM run verified
the continuous phase, ROM byte and ALU Y recurrence across that change.
Only the 74LS273 Q4→DAC08 B5 segment is photo-suggested; the decoder,
other seven DAC wires and sample clock are assumptions.

All **12 zero-error data orders** project a steady 1,800 Hz peak with
`B0`, a steady 2,100 Hz peak with `88`, and a **1,800→2,100 Hz** peak
change for all four controller selector classes without resetting the DSC
phase state. In the steady 640-sample projections, 1,800 Hz accounts for
0.711–0.747 of candidate code variance and 2,100 Hz for 0.286–0.359,
depending on bus order. The earlier Q4/Q5-swap order also has both peaks,
but has one data decision error and respective variance fractions 0.604
and 0.336. The selected bus's first 16 static and first eight dynamic codes
are checked against the saved PROM-execution reports before applying any
other permutation.

This is stronger **conditional transmitter consistency** than either test
alone: one fixed output-byte route can carry the real controller's dibit
phases and the provisional A1 2,100 Hz tone transition. It does not pick
one of the 12 full buses, establish that chip-1 bit 5 is the physical mode
command, measure the natural A1 timing, show segment-1 reversals at the line,
or trace the LS273 clock and DAC08 analog output. C2 remains open. The
[machine report](results/photo-dac-joint-data-tone.json) gives all 13
compared buses, their decision counts, tone fractions, four dynamic peaks,
and source hashes.
