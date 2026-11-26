# Post-visit receive state is a current-nibble codebook in three tested streams

The [replay](joint_mask04_postvisit_state_codebook.py) runs three different
eight-dibit reference waveforms through the same real-PROM mask04 receiver
fixture used for the matched-tail pulse test. Each waveform is converted to
64 ADC bytes, held for the established 47/46 visits per sample, and executed
for 96,047 microinstructions. It captures Q and all sixteen modeled Am2901
RAM bytes at each visit's final `3FE` row, for 9,000 visits total.

Across the three streams, every observed current ADC high nibble has exactly
one Q/RAM state at this capture point. The streams jointly cover all sixteen
high nibbles, yet produce only nine distinct state vectors. No post-`3FE`
state varies with prior dibits when the current high nibble is the same in
these tests. Thus this capture point does not supply a separate carrier-phase
or symbol-history state under the direct `D3EB=01` fixture.

This does not erase the [21-word transient carryover](JOINT-MASK04-RECEIVE-PULSE-CARRYOVER.md)
before the next ADC selection or the possible [U12 external latch](JOINT-MASK04-CARRYOVER-LATCH-PULSE.md).
It also does not establish that all receive modes or board connections lack
history. C3 remains open. Next test a photo-compatible U12 previous/current
pair with a causal phase tracker over rotated carrier starts and new payloads,
then follow the candidate decision into the controller/USART path. Keep the
latch and clock wiring explicitly assumed until independently constrained.

The [machine report](results/joint-mask04-postvisit-state-codebook.json)
contains each stream's trace and ADC hashes and the full 16-nibble Q/RAM
codebook. Reproduce from this directory with
`python3 g2/joint_mask04_postvisit_state_codebook.py`.
