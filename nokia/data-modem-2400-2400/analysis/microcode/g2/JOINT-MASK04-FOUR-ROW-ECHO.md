# Exact mask-04 own-TX echo shows no rapid selective attenuation in the four-row loop

The earlier [own-echo screen](JOINT-UPPER-ECHO-OUTPUT-SCREEN.md) used lower
mask `08` and a two-row receive fixture. Mask `04` is now the stronger
joint transmit/receive candidate because it retains ADC-dependent state
after all four receive rows. This experiment feeds its **own executed**
transmitter samples back into that complete loop, under labelled DAC,
analog echo and ADC assumptions.

For each call (`40`) and answer (`60`) selector, the controller-derived
A1→A2→A3→A4 stimulus runs through 1,248,256 real-PROM instructions.
The extracted 832 raw Y samples and full trace digest match the saved
[joint-map replay](JOINT-FOUR-ROW-RETENTION-TX.md) exactly. The first
photo-compatible DAC bus order from that replay provides 128 A4 sample
codes. A hypothetical own-echo path delays them by three 9,600-Hz sample
periods and scales them by one half. An independent remote reference DPSK
stream is scaled by one quarter. Zero, remote-only, echo-only and
remote-plus-echo controls are converted to complementary ADC bytes and
held for 47/46 table visits per sample. Each receive control executes
192,047 instructions, selects 6,000 ADC bytes and reaches the fourth row
6,000 times; all four controls take the same PC path.

At the center of each of the 128 ADC sample holds, the screen compares
Y at `3F8–3FA`, the latest `3ED` Y, Q and all 16 RAM bytes from the
complete row. The table shows remote-plus-echo minus remote-only response,
divided by injected echo RMS, in the first and last 32-sample windows.
Only bytes whose remote-only response exceeds 0.1 times remote-input RMS
in **all four** windows are listed.

| Byte | Call: first → last | Answer: first → last |
| --- | ---: | ---: |
| `Y3F8` | 1.009 → 1.048 | 1.009 → 1.028 |
| `Y3F9` | 1.078 → 0.990 | 1.078 → 1.144 |
| Q | 0.301 → 0.218 | 0.301 → 0.231 |
| R1 | 0.258 → 0.249 | 0.258 → 0.244 |
| R12 | 1.590 → 1.445 | 1.590 → 1.419 |

None halves its echo response by the last window. The other sixteen
captured bytes fail the remote-response threshold. This narrows a
**fixed-mode, direct-byte residual** interpretation under the exact
mask-`04` candidate, including its retained R1/R12/Q state. It does not
show that the board lacks an echo canceller: the DAC order, analog
coupling, ADC path and output coding remain hypotheses, the observation
is only 128 samples, and no controller-to-DSC train/freeze input or
verified line residual has been identified. C4 remains open. A
mode-qualified replay or another executed output site is needed before
assigning the receive loop an echo-canceller function.

The [machine report](results/joint-mask04-four-row-echo.json) includes
both selectors' transmitter/receiver hashes, input levels and all 21
channel ratios. Reproduce with
`python3 g2/joint_mask04_four_row_echo.py` from the microcode directory.
