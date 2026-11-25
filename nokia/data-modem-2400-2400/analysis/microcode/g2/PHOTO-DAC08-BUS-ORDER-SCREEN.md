# A matching DAC B5 tone bit does not imply a matching eight-bit DAC code

The [DED 3558 front photo](../../../photos/PXL_20261123_114854803.jpg)
suggests one DAC08 data segment, 74LS273 Q4→DAC08 B5. The
[bus-order runner](photo_dac08_bus_order_screen.py) holds that assignment and
tests three simple one-to-one hypotheses for the other Q/B wires: reverse
Q1…Q8 to B8…B1, rotate Q1…Q8 one B position, or exchange only Q4/Q5.
It also tests ordered ALU-Y→LS273-D bits and a Y7/Y4 input swap that places
the earlier tone-rate Y7 bit on Q4. **Only Q4→B5 is photo-suggested; all
other assignments and the latch clock are untraced.**

The fixture is the [A1 CD4094 D0/D3 candidate](PHOTO-CD4094-BIT-SWAP-TONE.md):
held D127=`88`, q3, a 9,600-sample/s gate, one oscillator period per
microinstruction. Both Am27S31 banks execute 740 `129/12A` visits; every
projected source byte matches the real-PROM trace. All 32 divider start
phases are spectral rotations. The upper-bank results below use the proposed
DAC08 input code, rather than one bit:

| Y→LS273-D mapping | LS273-Q→DAC08-B mapping | `129` full-code peak / 2,100 Hz fraction | `12A` full-code peak / fraction |
| --- | --- | --- | --- |
| ordered | reverse | 4,800 Hz / 0.065 | 2,100 Hz / 0.235 |
| ordered | rotate by one | 4,800 Hz / 0.146 | 2,100 Hz / 0.332 |
| ordered | swap Q4/Q5 | 2,100 Hz / 0.336 | 2,100 Hz / 0.609 |
| Y7/Y4 swapped | reverse | 4,800 Hz / 0.061 | 2,100 Hz / 0.247 |
| Y7/Y4 swapped | rotate by one | 4,800 Hz / 0.046 | 2,400 Hz / 0.168 |
| Y7/Y4 swapped | swap Q4/Q5 | 3,300 Hz / 0.053 | 2,400 Hz / 0.002 |

With Y7 routed to Q4, DAC B5 peaks at 2,100 Hz in all three full-byte
orders at `129` and `12A`. Yet **none of the three `129` full DAC codes peaks
at 2,100 Hz**. The sole `12A` full-code survivor in that group is the
reversed bus, with only 0.247 of its variance at 2,100 Hz; its raw source is
already almost a phase ramp. In the ordered-input cases, DAC B5 peaks at
1,800 Hz for `129` Y or 2,400 Hz for `12A` Y, even where the full byte peaks
at 2,100 Hz. The [machine report](results/photo-dac08-bus-order-screen.json)
records all 24 bank/site/bus cases, B5 spectra, first codes, execution digests
and source/photo hashes.

This makes the earlier B5-only 2,100 Hz observation a poor selector for a
complete DAC route. These three full-bus assignments are hypotheses, not an
exhaustive net search. An analog filter, different D-bit order, staged latch
or other output site could still produce the line signal. The next useful
test needs a tighter photo-compatible data/clock mapping or a distinct
ROM-to-output path, while retaining the controller-state and symbol tests.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/photo_dac08_bus_order_screen.py
```
