# One raw PROM edge selects the A1 ROM window but runs too fast for DAC samples

The [edge-and-latch replay](photo_12c_prom_edge_latch.py) uses the executed
8031 A0/A1 frames under a candidate four-CD4094 cascade. Logical chip 1
Q8→D0 supplies D127=`88` in A0 and `81` in A1; chip 0, 2 or 3 supplies
held D12C=`7A`, `02` or `80`. Under the q3/held-I0/upper-ROM hypotheses,
A0 stays in the first loop while A1 makes 613 selected PC12E reads in each
3,000-microinstruction run. The physical CD4094 and DSP routes are untraced.

For each of those three paired runs, the screen checks both edge directions
on all 32 raw U10/U11/U17/U18 PROM data bits. Twelve bit/edge choices fire
at every A1 `12E` visit. Only **U18 D1 rising** also has **no edge in the
recurring A0 `129` loop** and at most seven other A1 edges:

| A1 D12C | A1 U18 D1 edges at `12E` | Other A1 / A0 edges | Distinct captured `12E` Y bytes | Candidate DAC B5 transitions |
| ---: | ---: | ---: | ---: | ---: |
| `7A` | 613 / 613 | 7 / 6, all during setup | 102 | 347 |
| `02` | 613 / 613 | 7 / 6, all during setup | 102 | 18 |
| `80` | 613 / 613 | 7 / 6, all during setup | 2 | 612 |

The seventh A1 edge occurs at `09C` just before the second loop; all later
U18 D1 rising edges are at `12E`. The candidate B5 column assumes ALU Y7
drives 74LS273 D4, whose Q4 may drive the photographed DAC08 B5 pad. Only
the Q4→B5 segment is photo-suggested; the Y7→D4 and clock wires are not.
The [machine report](results/photo-12c-prom-edge-latch.json) records every
aligned bit, extra edge, sample-code count, B5 transition count and trace
digest.

This is a useful **mode-qualified microinstruction strobe candidate**, not
a recovered DAC clock. U18 D1 also has a tentative Am2901 register-address
role, and no connection to the DAC-side 74LS273 clock is established. One
edge per four-word loop would run at 0.9–3.6 MHz if the 14.4 MHz oscillator
supplies one microinstruction per `k=1…4` periods. Reaching the proposed
9,600 DAC samples/s would require a further divider or qualified transfer.
The captured Y bytes and one candidate DAC bit do not yet form a measured
1,800/2,100 Hz line signal or dibit-dependent modulation.
The [divided-strobe tone test](PHOTO-12C-DIVIDED-STATE-LATCH.md) now checks
the three held A1 frame bytes at hypothetical 9,600-sample/s clocking; none
peaks at 2,100 Hz under the tested integer clock ratios.
