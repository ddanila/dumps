# Complementary DAC output polarity does not distinguish the joined fixed readout

The [DED 3558 front photo](../../../photos/PXL_20261123_114854803.jpg)
shows separate tracks leaving the DAC08 analog-side pads: the pin-2
region meets a nearby vertical resistor, while the pin-4 region has a
leftward track. The [DAC08 datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/dac08.pdf)
labels pins 2 and 4 complementary current outputs. The photographs do
not trace either path through the later analog stages to the line, and
an amplifier could invert the signal again. The sign of the candidate
line waveform is therefore an explicit alternative.

This [test](joint_mask04_dac_output_polarity.py) reconstructs the
838-sample Y7 source from the verified phase recurrence and hash-checks
both its bits and nominal B5/filter PCM against the saved full real-PROM
transmitter run. It negates that centered PCM before the hypothetical
complementary ADC, then executes **768,047 real-PROM receive words** for
each call/answer selector. The three capture pairs and ADC-margin rule
remain frozen; no label is used to choose a pair.

| Selector | Independent reference errors | Frozen 46/93 wrong / unknown / 63 | Recovered line bytes | ADC-margin wrong / unknown |
| --- | ---: | ---: | --- | ---: |
| `40` call | 0 | 0 / 0 | `62 DE 61 9D 7C 5F E5 E2` | 1 / 0 |
| `60` answer | 0 | 0 / 0 | `A5 C2 4C 58 52 47 65 B4` | 0 / 0 |

The inverted-waveform receive traces differ from the nominal traces.
The fixed pair nevertheless recovers all 32 data dibits and the same
eight controller-scrambled bytes under either output sign. The call-side
margin error moves from symbol 44 in the nominal run to symbol 56 here,
still selecting the later `94/141` pair. These results do not identify
which DAC current output or amplifier path Nokia uses. They show only
that this candidate digital handoff is **insensitive to sign** in the
tested fixture; gain and bias sensitivity remains open.

The [machine report](results/joint-mask04-dac-output-polarity.json)
records both signal and ADC hashes, receiver trace digests and frozen
scores. Reproduce from the microcode directory with
`python3 g2/joint_mask04_dac_output_polarity.py`. C2 and C3 remain
conditional on the untraced data, clock, analog and receive routes.
