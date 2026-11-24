# Single-byte startup RAM does not animate the bit-sensitive 38E path

The local instruction-bit searches kept all Am2901 RAM bytes at zero. That
could hide a phase or filter state initialized elsewhere on the board. This
experiment tests that possibility for the q1 photo-constrained mapping with
the hypothetical `I1 = !10.5` assignment, the only one-bit variant that
changed a candidate output byte for controller bits 0 and 1.

[`startup_ram_bit_sensitive.py`](startup_ram_bit_sensitive.py) runs the real
control PROMs for 512 cycles with Q=5 and the real 8031 scrambler bits offered
at the hypothetical D38E input. It changes one startup RAM byte at a time:
16 spread values for each of R0–R11 and R14–R15, and all 256 values for R12
and R13, which retained their seeded values in the initial coarse screen.
The other 15 RAM bytes remain zero in each run. All **736** cases complete,
visit 38E **39** times, make **121** ALU-selected ROM reads and contain **38**
complete input groups. Every case has exactly one ROM-address pattern and one
candidate output pattern for each repeated bit value. All cases distinguish
the two bit values at the candidate output byte, but **none** develops a
changing sequence within repetitions of the same bit.

The [saved report](results/startup-ram-bit-sensitive.json) lists each startup
value, trace digest, final Q/R12/R13 and pattern counts. This is a scoped
single-byte sensitivity result, not a proof that startup state cannot matter:
combined RAM values, mode setup writes, other initial Q values and different
instruction/input mappings remain open. It does make a missing value in one
RAM byte a poor explanation for the fixed-output result on this particular
controller-fed path. The next search should change a shared routing or
control assumption rather than adjust another isolated startup byte here.
