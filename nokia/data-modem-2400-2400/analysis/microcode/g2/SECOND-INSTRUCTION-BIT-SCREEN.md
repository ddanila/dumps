# A second instruction-bit change does not make the 38E path a carrier

The [one-bit screen](INSTRUCTION-BIT-NEIGHBORHOOD.md) found four mapping
variants where a hypothetical instruction assignment `I1 = !10.5` changes
the candidate ALU-Y byte between controller bits 0 and 1. This experiment
keeps that assignment and changes one more Am2901 instruction input: I2–I6
or I8, using every bit of PROMs U10 and U11 in either polarity. It repeats the
same photo-constrained Q=5, zero-RAM fixture and the candidate connection
from the real 8031 controller scrambler to the D read at 38E. Neither I1 nor
the second bit has a traced board net here.

[`second_instruction_bit_screen.py`](second_instruction_bit_screen.py) runs
960 variants for 512 real-PROM cycles. All complete. The 539 cases with more
than ten 38E visits and more than ten ALU-selected Am27S31 reads are traced
again; each has 38 complete input groups. Groups are closed by the next 38E
read, and the first three complete groups are omitted from the repeated-bit
comparison. None of the 539 changes its ROM-address pattern or candidate
output pattern between repetitions of the **same** bit. Seventy select a
different fixed ROM-address pattern for 0 and 1; 351 give different fixed
candidate output bytes. These are bit-dependent lookup choices, not an
advancing carrier sample sequence.

For example, q1 with `I1 = !10.5` and `I2 = 10.0` reads ROM addresses
`106,100,105,106` for each completed 0-bit group and `100,100,105,106` for
each completed 1-bit group. Its candidate output at 39E is 6 for 0, while
the one at 392 is 5 for 1. The
[saved report](results/second-instruction-bit-screen.json) retains this
representative group's first eight visits, all 539 shortlisted mapping
choices and their trace digests, and the path-class counts for all 960 runs.

This excludes a sustained changing lookup or output **within this two-bit
neighborhood and fixture**. It does not identify the physical instruction
wiring, the actual controller input site, the DAC08HP latch route or other
multi-bit mappings. Since even bit-dependent candidates lack sample evolution,
the next useful experiment should change a shared assumption such as the
input path, startup mode or field mapping, rather than refine this same
38E/Q=5 neighborhood further.
