# The `12A` line candidate survives fixed gain but needs a precise sample phase

The earlier [analog holdout](JOINT-MASK04-12A-ANALOG-HOLDOUT.md) scaled
each new payload independently to peak 110 before the reference
decoder. This [follow-up](joint_mask04_12a_fixed_gain_phase.py) makes
that gain test stronger. For each selector and candidate DAC bus, it
calibrates a single gain on the controller-fed eight-zero-byte stream
at +6 samples. It then replays the same two saved nonzero eight-byte
payloads per selector with that gain fixed. It extends the held final
data by six samples to test alignment −7 through +12, and applies
0.75, 1.0 and 1.25 level multipliers without refitting per payload.
Every original 846-byte `12A` prefix hash matches its saved run.

At +6 samples, **all 24 bus/payload streams decode 64/64 dibits** at
each of the three levels: 4,608 correct decisions across the three
level cases. At +5, 18/24 streams remain exact; all six failures are
the second answer payload at decision index 62. At +7, none of the 24
streams is exact (104–108 total wrong dibits across the 24 streams,
depending on level). The calibrated gains span 0.9433–0.9511 across
the twelve selector/bus combinations.

This supports the candidate analog gain on new data without
payload-specific normalization, while narrowing the viable line
sampling phase. The same two nonzero payloads were used in the prior
holdout; they are new relative to the zero-run gain calibration, not
a new independent data set for selecting Q. The DAC bus, latch edge,
sample clock, analog filter and physical line remain assumed. A
known-carrier reference decoder is not the DSC receive/USART route.
Keep C2/C3 open and G2 active; next constrain the latch timing with
photo-compatible clock alternatives and test carrier offset without
refitting the frozen route.

The [machine report](results/joint-mask04-12a-fixed-gain-phase.json)
contains all 1,440 reference scores, calibration gains and source
hashes. Reproduce with `python3 g2/joint_mask04_12a_fixed_gain_phase.py`
from the microcode directory.
