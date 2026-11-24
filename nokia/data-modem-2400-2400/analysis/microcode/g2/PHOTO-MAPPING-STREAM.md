# Controller bitstream across five photo-compatible mappings

[The executable screen](photo_mapping_stream_screen.py) runs five Am2901
field candidates against the same real 8031-derived 128-bit stream and real
DSC 2847 control PROMs. It retains the photo candidate A2=`10.7`, A3=`10.6`,
I7/A0=E4 high and I0/A1=E2 low, plus the existing q3-derived branch,
condition, ROM gate and D38E input fixture. Initial Q is 5 and RAM is zero.
The [saved report](results/photo-mapping-stream-screen.json) contains source
hashes and per-run trace digests. All five consume all 128 bits cleanly.

| Mapping | Recurring PCs | PCs with changing ALU Y after first input | Recurring ROM reads | Candidate output values |
| --- | ---: | --- | --- | --- |
| q1 photo-swapped | 16 | 38E: 251, 252 | None | 392: 11 |
| q2 photo-swapped | 12 | None | None | No 392/396 visits |
| q3 photo-swapped | 16 | 38E: 251, 252 | None | 392: 11 |
| q4 photo-swapped | 12 | None | None | No 392/396 visits |
| fitted-swapped | 12 | None | None | 396: 1 |

This rules out the *scoped Q=5 controller-bit path* as the demonstrated
transmitter under all five mappings: no repeated ROM lookup or changing
candidate sample follows the input. It does not exclude the mappings as a
whole. The same controller bit may enter at a different D site, and other
startup states, mode commands, ROM enables, output strobes or timing phases
can enter different microcode paths. None of those physical connections is
established by this screen. The next execution search should vary the
startup/command interface and retain any path with stateful, symbol-dependent
samples for a physical output-net check.
