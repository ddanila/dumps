# Held controller `A1` mode does not make the `3FC` RAM return cancel echo

The earlier [mode-`01` `3FC→3FD` challenge](JOINT-MASK04-RAM-CARRY-3FD-ECHO-SCREEN.md)
found a delayed-input code, not a falling echo residual. This
[replay](joint_mask04_a1_ram_3fc_echo.py) adds the actual controller's
observed `A1` third-frame byte as a **hypothesized** held `3EB` input.
It keeps the same real-PROM q3/mask-04 mapping, complementary ADC
schedule, previous-carry TEST assumption, 3-sample-delayed high-nibble
RAM return at `3FC`, and `3F9` Y-high write latch. The four stimuli
are zero, own echo, independent remote, and their mixture; each has a
same-input write-only control. Training writes stop after 128 samples,
then a 64-sample common-zero tail runs. All eight 288,047-word traces
sustain the 9,000-visit receive loop.

Mean absolute unsigned `3FD` Y-byte contrasts over all selected visits:

| Route and contrast | Early 32 samples | Late 32 training samples |
| --- | ---: | ---: |
| Write-only, own versus zero | 0 | 0 |
| Write-only, mixed versus remote | 0 | 0 |
| RAM return, own versus zero | 4.971 | 5.973 |
| RAM return, remote versus zero | 4.011 | 4.501 |
| RAM return, mixed versus remote | 7.477 | 8.480 |

All 46 fixed sample phases give the same pattern: own contrast rises
from 5.0 to 6.0, and mixed-minus-remote rises from 7.5 to 8.5.
No phase has both echo contrasts falling while remote response remains.
The return differs from its write-only control for exactly 141 visits
in the common-zero tail for every stimulus, the three-sample read lag.
The `A1` mode changes the size of the output code contrasts relative to
the saved mode-`01` fixture, but does not show selective training
attenuation at this candidate output.

The frame-to-`3EB` connection, external RAM mux, TEST source, ADC
clock and `3FD` output latch are untraced. Unsigned Y-byte contrast is
a diagnostic, not an analog residual. This excludes C4 for the stated
combined hypothesis only; C3/C4 and G2 remain open. Next audit the
pre-`3FC` R10 and pre-`3FD` R5 operands in this `A1` run to see whether
the mode introduces a varying consumed coefficient, or try another
photo-compatible return/output path with the same controls.

The [machine report](results/joint-mask04-a1-ram-3fc-echo.json)
records every trace/input/output hash, RAM activity and phase score.
Reproduce with `python3 g2/joint_mask04_a1_ram_3fc_echo.py` from the
microcode directory.
