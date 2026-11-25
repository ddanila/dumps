# Unmodified controller frame lanes are not exact PC12C tone steps

The [PC12C execution](photo_12c_controller_frame_steps.py) takes the four
frame bytes produced by the unchanged 8031 main-loop runs for selector
classes `00`, `20`, `40` and `60`. At the first line-output iteration those
frames are `D0 47 A1 22` or `D0 42 A1 BA`. Each of the six distinct bytes is
held, in turn, at candidate DSC2847 input `D12C` after `D127=81` enters the
second q3 ROM loop. This is a **direct frame-lane wiring hypothesis**, not a
traced controller-to-DSP connection or an identified data-2400 command.

All six 3,000-microinstruction runs select the offered byte at `12C`, and
each selected `12E` ROM address follows `100 + ((1 + n×D12C) mod 256)`.
Odd bytes `47` and `A1` reach address `100` and then the `084` wait after
137 and 159 ROM reads. Four even bytes keep the loop running for all 613
ROM reads in the bounded run. Their implied phase rates at an *assumed*
9,600 sample/s gate are:

| Held frame byte | 1 oscillator period/microinstruction | 3 oscillator periods/microinstruction |
| --- | ---: | ---: |
| `22` | 1,875 Hz | 3,825 Hz |
| `42` | 3,075 Hz | 2,175 Hz |
| `BA` | 4,425 Hz | 1,725 Hz |
| `D0` | 3,000 Hz | 4,200 Hz |

These are folded frequencies of the modular **phase address**, not line
tones or DAC codes. None has the exact phase step `±48` or `±56` needed for
1,800 or 2,100 Hz under these two integer-ratio clock hypotheses. The
nearby 1,725/1,875/2,175 Hz values do not establish modem tone selection.
The [report](results/photo-12c-controller-frame-steps.json) retains every
trace digest, read count, wait point and derived step.

This closes the unmodified held-frame-byte route to PC12C in the tested
fixture. A decoded or time-varying frame input, other clock, different
mapping, or another ROM/output path remains testable without new continuity
measurements. The controller bitstream already changes this loop's internal
phase address; its physical input route and DAC-bound output remain open.
