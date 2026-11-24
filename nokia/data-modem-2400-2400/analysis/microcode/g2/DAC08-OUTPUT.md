# DAC08HP output-converter candidate on DED 3558

The [DED 3558 front photograph](../../../photos/PXL_20261123_114854803.jpg)
shows a 16-pin device near the lower analog section marked `DAC 08` and `HP`
(approximately x=1100–1300, y=3250–3550 in the 3072×4080 original). The
package marking is consistent with **DAC08HP**. This is the photographed
output-converter candidate that was missing from the earlier G2 evidence.
The part identification is visual; its electrical connections have not been
measured. The original photo is recorded in
[the photo manifest](../../../photos/manifest.json) under SHA-256
`f11810e13a5b4f334333bbd79f59badb258d497653bc9e109f4d5bb5a012bf9d`.

The [Analog Devices DAC08 datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/dac08.pdf)
identifies DAC08HP as a 16-lead plastic DIP **8-bit D/A converter**. Its
digital input pins are 5–12: B1 (MSB) at pin 5 through B8 (LSB) at pin 12.
Pins 2 and 4 are complementary current outputs. The chip itself has no
separate input and DAC registers or WR1/WR2-style transfer protocol. In the
photo a 74LS273 register sits next to its digital-input side, and visible
front-side traces run between their pad regions. That makes the 74LS273 a
candidate sample-code latch. Individual data bits, the latch clock, DAC08
reference and current-output route still need tracing or explicit hypotheses.

This changes the emulator target. A useful transmitter test should capture
the eight bytes presented to that external latch under a proposed strobe,
then interpret the DAC08 input code as an output sample. The earlier
[DAC0830 sink](../assumed/DAC-OUTPUT.md) remains a labelled counterfactual:
the photographed chip does not support its two-stage input/DAC-register
timing. The candidate DAC08 narrows the output hardware, but it does not by
itself connect any particular Am2901 Y word to the latch, establish sample
rate, or demonstrate a carrier.

## Explicit latch hypothesis and replay

The [SN74LS273 datasheet](https://www.ti.com/lit/ds/symlink/sn74ls273.pdf)
specifies eight rising-edge D flip-flops with active-low clear. The
[digital-only probe](dac08_latch_probe.py) tests one candidate: the Am2901
ALU Y byte drives the latch D pins, a rising clock occurs at the selected
microcode word, and Q1–Q8 map in order to DAC08 B1–B8. Neither that clock
nor the individual bus connections have been traced on the board. Its saved
[result](results/dac08-latch-probe.json) is a proposed *DAC input code*, not
a measured line-output waveform.

In 2,048 real-PROM cycles, a clock at 12C captures 500 q1 bytes, eventually
repeating a 20-code sequence. This fixture consumes no controller bits.
Clocking the q3 path at 392 captures 57 copies of code 11 after it consumes
128 real-controller scrambler bits. The fitted path clocks at 396 and captures
128 copies of code 1 from the same 128-bit stimulus. These two controller-fed
paths cannot yield a modulated signal under this latch hypothesis. The q1
sequence is changing, but without controller-symbol dependence or a traced
clock/output route it is not a demonstrated transmitter. Next experiments
should vary the latch data source and clock phase, then test any surviving
path against the transmitter checks in [PLAN-2.md](../PLAN-2.md#3-acceptance-for-g2).

The [startup-RAM screen](ram_seed_output_screen.py) tests another concrete
alternative to that fixed q3 code. With Q=5 and the same controller-bit
fixture, it changes each initial Am2901 RAM byte independently through nine
nonzero values. None of the 135 non-RAM13 cases changes the 392 latch code or
control-flow counts. A complete 256-value sweep of RAM13 shows a more precise
dependency: 254 seeds capture one constant code, `(11 + RAM13) mod 256`, for
all 17 visits in 512 cycles. RAM13 is never written in these runs. Seeds 249
and 250 instead leave the recurring path at the branch at 390, visit the
controller input once, capture no code at 392 and reach 084. The
[saved result](results/ram-seed-output-screen.json) includes source hashes and
per-seed outcomes. This rules out a changing 392 output from any *single*
initial RAM-byte change in this fixture; simultaneous state changes, other
clock sites and other input routes remain open.
