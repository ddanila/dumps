# The candidate controller latch gate survives a longer real-PROM transmitter run

The [controller frame timing](CONTROLLER-A2-LATCH-GATE-TIMING.md) holds
third-frame-byte bit 0 low across A2 for 61,938/61,772 modeled 8031 ticks.
Under the explicit 104-tick-per-DAC-sample clock hypothesis, that is
596/594 candidate samples. The previous [joint-map DAC screen](JOINT-MASK04-TX-PROM-EDGE.md)
tested only 64 A2 samples. This [extended replay](joint_mask04_a2_le_timed.py)
runs the **same fixed mask-`04` field map** for 32 tone symbols, 74 A2
symbols, 32 reversal symbols and 32 data symbols without resetting the DSC.
Each selector executes 2,040,256 real-PROM microinstructions, traverses
510,054 candidate U10 D2 edge pairs, and captures 1,360 divided-clock DAC
samples. Both runs end cleanly.

The proposed 74LS373 C/LE gate falls at the first A2 sample and rises after
the observed controller interval, rounded to a DAC sample. Since 74 A2
symbols span 592 samples, the latch would still hold the first **four A3
samples** for selector `40` or **two** for selector `60`. The test varies
release by one sample in either direction. While C/LE is low, the candidate
DAC code is the last A1 code; when high, it follows the captured real-PROM
code. [TI's 74LS373 datasheet](https://www.ti.com/lit/ds/symlink/sn74ls373.pdf)
supports that transparent/hold behavior, but the Nokia bit-to-C/LE and data
connections are assumed.

| Result across 2 selectors × 6 candidate DAC buses × 2 latch phases × 3 release offsets | Observed |
| --- | ---: |
| A1 spectral peak | 2,100 Hz in all 72 cases |
| Late-A2 RMS / late-A1 RMS, gate open throughout A2 | 0.998245–0.998451 |
| Late-A2 RMS / late-A1 RMS, controller-timed latch hold | 0.000000 at reported precision |
| A3/A4 reference decisions after hold | **0 errors of 62 per case** |

The zero-error result includes the first A3 symbol with its two or four held
samples. It shows this *specific* controller-bit/74LS373 timing candidate can
carry tone, silence, reversals and data through one uninterrupted PROM run
under all tested DAC bus and latch-phase variants. A changing-code pass-through
control remains nearly as loud in A2 as A1.

This is not a measured Nokia line output. The CD4094-to-74LS373 enable wire,
74LS373 data route, 74LS273 strobe, DAC08 bus, analog filter and connector
route remain untraced. The controller and DSC are not executed on a shared
instruction clock; their frame event is projected onto the DSC schedule by
the assumed oscillator dividers and an aligned A2 start. The 1,950 Hz Q=1
bandpass and independent reference decoder are external models. C2 and G2
remain open until the output route is independently constrained and the
remaining acceptance checks pass.

The [machine report](results/joint-mask04-a2-le-timed.json) records all 72
metrics and both PROM trace digests. Reproduce from the microcode directory
with `python3 g2/joint_mask04_a2_le_timed.py`.
