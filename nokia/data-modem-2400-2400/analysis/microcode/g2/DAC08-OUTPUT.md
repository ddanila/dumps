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
