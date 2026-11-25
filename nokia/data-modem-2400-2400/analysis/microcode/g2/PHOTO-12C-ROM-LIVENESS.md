# The second-loop ROM operand is erased at the next `12D`

The [paired-bank replay](photo_12c_rom_liveness.py) enters the q3
`12C–12F` loop with held D127=`81`, then tests D12C=`7A`, `02` and `80`
from the candidate A1 CD4094 frame, plus `88` as a tone-step control.
Only the Am27S31 bank selected at PC12E changes between each pair; PC129
stays in the upper bank. The controller-to-D connections, bank driver,
held-I0 circuit and q3 field mapping are hypotheses.

Each of the eight real-PROM runs completes 3,000 microinstructions and
selects 613 PC12E operands. Every ROM address and PC12E ALU value follows
the executed phase relation. The paired results are:

| Held D12C | Different ROM / `12E` Y bytes | Different `12F` Y and next-`12C` R0 values | Different full states after `12D` |
| ---: | ---: | ---: | ---: |
| `7A` | 598 / 613 | 165 / 613 | 0 / 613 |
| `02` | 600 / 613 | 163 / 613 | 0 / 613 |
| `80` | 613 / 613 | 0 / 613 | 0 / 613 |
| `88` | 613 / 613 | 114 / 613 | 0 / 613 |

Before `12D`, the only modeled state difference is R0, carrying the
preceding `12F` result. From the second loop visit onward, `12D` writes
R0=`00`; after each `12D`, the complete modeled RAM, Q, ALU flags, stack
and next PC agree across banks. The PC path also agrees throughout, and
neither bank reaches candidate output `392` or `39E`. The
[machine report](results/photo-12c-rom-liveness.json) includes read counts,
paired state comparisons and trace digests.

Under this mapping and fixture, a downstream state machine cannot observe
which ROM bank was read **after** `12D`. An external output latch could still
capture the changing `12E` ALU Y, the carry-dependent `12F` Y, or the retained
R0 before `12D` clears it. That narrows the required sample window for a
DAC08 route; it does not establish a latch clock, output bus, or waveform.
