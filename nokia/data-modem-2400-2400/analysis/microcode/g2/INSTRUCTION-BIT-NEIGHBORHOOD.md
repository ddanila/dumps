# One-bit instruction-map neighborhood at the controller input

The existing q1–q4 Am2901 instruction maps were selected using a proposed
arithmetic identity, not traced pin connections. This experiment asks whether
one different PROM data lane on an instruction input would turn the
controller-fed 38E path into a changing lookup or output sequence. It is a
local mapping search, not a recovery of the physical instruction wiring.

[`instruction_bit_neighborhood.py`](instruction_bit_neighborhood.py) changes
one of I1–I6 or I8 at a time to each bit of U10 or U11, in either polarity, in
the q1–q4 photo-swapped and fitted-swapped mappings. The other fields retain
their photo-constrained candidate assignments. All 1,120 variants run for 512
real-PROM cycles with Q=5, zero initial RAM and the same hypothetical D38E
connection carrying bits from the real 8031 controller scrambler. The first
pass selects cases with more than ten D38E visits and more than ten
ALU-selected Am27S31 reads; 98 pass. The second pass traces those 98, assigning
ROM addresses and candidate ALU-Y outputs to each input bit. A group counts
only when the *next* D38E read closes it; this discards the incomplete final
group at the cycle limit. The first three complete groups are excluded when
comparing repeated-bit patterns, to allow for startup transients.

All 1,120 runs finish cleanly. Each shortlisted trace has 38 complete input
groups. None of the 98 changes its post-input ROM-address pattern or its
candidate output pattern between repetitions of the **same** bit. None has a
different ROM-address pattern for 0 versus 1. Fifty-three have different
output-site/byte pairs for the two bit values, but only four change the byte
itself. These four are q1–q4 with hypothetical `I1 = !10.5`: bit 0 visits
39E with Y=11; bit 1 visits 392 with Y=5. Each value remains fixed across
repetitions, so this is a symbol-level distinction, not the varying sample
sequence required of a demonstrated transmitter. One representative
`I1 = !10.1` path reads addresses 100, 105, 106 on every completed 0-bit
group, illustrating why a raw count of repeated ROM reads is insufficient.

The [saved report](results/instruction-bit-neighborhood.json) contains every
shortlisted mapping, source and trace digest, with per-bit pattern counts and
the first eight complete groups. These results narrow a single-bit neighborhood
around five proposed mappings under one Q, RAM, ROM-enable, branch and input
fixture. They do not exclude multi-bit wiring changes, different clock phases,
other controller input routes or a different physical output capture. In
particular, U10/U11 proximity to the Am2901 makes them candidate sources, but
the individual I-bit nets have not been traced. The next mapping search should
couple instruction bits that share a plausible physical register route, or
test a separate input/output path, rather than treating one fixed lookup loop
as the carrier.
