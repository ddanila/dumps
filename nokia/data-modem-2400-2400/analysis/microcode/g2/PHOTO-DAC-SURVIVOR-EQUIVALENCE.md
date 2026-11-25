# Six surviving DAC orders share the same upper five code bits

The [nonperiodic dibit holdout](PHOTO-RANDOM-DIBIT-VALIDATION.md) left six
photo-compatible DAC08 bus orders. This [comparison](photo_dac_survivor_equivalence.py)
applies all six to the 832 candidate `129` sample bytes in each joined GPC and
GPA A1–A4 transmitter stream. It regenerates the bytes and checks the saved
full-PROM sample digest before comparing them.

All six orders map the same five source bits to DAC code bits 3–7. They differ
only in how source bits 1, 3 and 5 reach the three least significant DAC code
bits. Consequently, **every candidate sample has the same upper five bits**.
The largest observed difference between any two complete 8-bit codes is just
3 counts out of 255, in both controller modes. Across the 15 order pairs,
the RMS difference is 0.57–2.29 counts for GPC and 0.58–2.27 for GPA.
The [saved report](results/photo-dac-survivor-equivalence.json) includes all
pairwise differences, source hashes and sample digests.

This explains why more tone-frequency or dibit-decision screens using the
same candidate output will struggle to identify the low-bit order: those
screens primarily see the common upper-five-bit waveform. A trace of one
of the three disputed LS273-to-DAC08 low-weight connections, or an
independent high-precision analog capture, is a more discriminating test.
The photo currently supports only Q4→B5 as a candidate, and the assumed
Y-to-latch bus, sample clock, analog stage and physical line output remain
unverified. The six code orders remain separate hypotheses, but their
common waveform should be used to test larger clock and output-route
questions without treating this small bus ambiguity as a blocker. C2 is open.

Reproduce from the microcode directory with
`python3 g2/photo_dac_survivor_equivalence.py`.
