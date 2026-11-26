# A broader analog candidate carries new `12A` data

The [extended alignment test](JOINT-MASK04-12A-EXTENDED-SHIFT.md) left
one wrong call dibit under the original Q=1 line filter. A
[bounded screen](joint_mask04_12a_analog_screen.py) varied the assumed
bandpass center (1650/1950/2250 Hz), Q (0.5/1/2/3), output peak
(80/110/127) and +6/+7 sample phase, preserving both real-PROM
controller-fed zero-run streams and all six photo-compatible DAC buses.
It reproduced the saved Q=1, 1950 Hz, peak-110, +6 decisions. At Q=0.5,
all three centers and all three peaks give **0/64 wrong call and 0/64
wrong answer** reference dibits at +6 on every bus. The screen selected
1950 Hz, Q=0.5, peak 110, +6 as one fixed candidate before new data.

The [holdout replay](joint_mask04_12a_analog_holdout.py) then used two
new nonzero eight-byte controller payloads in each selector mode. It
kept the selected filter, scale and sample phase fixed. For each of
the four streams, all six buses yielded **0/64 wrong** known-carrier
reference dibits: 24 bus/stream scores, or 1,536 dibit
decisions. The Q=1 control failed the first call payload by 3–4 dibits
and the second answer payload by 2; its other two streams were exact.

This is a reproducible, ROM-sensitive transmit waveform candidate that
survives new data and resolves the earlier call-line reference error.
The DAC bit order, latch phase, analog filter and gain are still
photo-compatible assumptions. The reference receiver supplies its own
carrier; no executed DSC decision or USART RxD path has been shown for
these payloads. Keep C2/C3 open and G2 active. A useful next test is
to vary sample phase, gain and carrier offset without refitting this
candidate, then join an executed receive/USART readout under explicit
photo-compatible wiring assumptions.

The [screen report](results/joint-mask04-12a-analog-screen.json) and
[holdout report](results/joint-mask04-12a-analog-holdout.json) contain
per-bus decisions and trace hashes. Reproduce from the microcode
directory with `python3 g2/joint_mask04_12a_analog_screen.py` and
`python3 g2/joint_mask04_12a_analog_holdout.py`.
