# Running the two Am2901 slices with distinct instructions

The two [facing-pad candidates](PHOTO-SLICE-LINK.md) suggest that U8 I4 may
share U2 I1's signal and U8 I6 may share U2 I2's signal. To test the
implication, the emulator now accepts an explicit, provenance-owned
`slice_instruction` hypothesis. It runs U2 and U8 as separate 4-bit Am2901s,
with those two U8 bits copied from U2's instruction. Remaining instruction
bits are common, and carry/shift pins use the ordinary 8-bit cascade as a
separate assumption. With no links, this model matches the original 8-bit
model across all 512 instruction codes in sampled states. When one slice
requests a shift bit that the other does not drive, the model requires an
explicit fallback input level; the probe tests both 0 and 1.

The [probe](split_slice_probe.py) uses the real four-PROM control store, all
five photo-constrained mappings and the existing controller-bit fixture. It
sweeps every initial Q byte for 512 cycles, then runs Q=5 for 1,580 cycles
with the controller bitstream. The [saved report](results/split-slice-probe.json)
contains the mapping/scenario hashes and trace digests.

| Mapping | Q seeds entering recurring input, of 256 | Maximum selected ROM reads in a 512-cycle seed run | Variable candidate output sites in the Q=5 controller run |
| --- | ---: | ---: | ---: |
| q1 | 32 | 5 | 0 |
| q2 | 32 | 118 | 0 |
| q3 | 32 | 5 | 0 |
| q4 | 32 | 5 | 0 |
| fitted-swapped | 32 | 3 | 0 |

In every Q=5 run, all 128 offered controller bits are consumed. After the
first input, none of the five split-slice runs selects an Am27S31 byte as an
ALU operand, and every visited candidate output PC has one fixed Y byte.
The shared-instruction controls show the same lack of post-input ROM work
and changing output. Split-slice execution does change internal register
activity, so the new candidate wiring reaches the datapath, but these two
links alone do **not** produce a transmitter under this fixture. Neither the
Q seed sweeps nor either Q=5 controller run actually requests an undriven
cross-slice shift bit, so the fallback input level does not affect these
results.

The q2 seed with Q=0 accounts for its 118 reads: all are at microcode word
`129`, from one Am27S31 address `1F1`, returning `30` and a fixed ALU Y of
`30` (hexadecimal). It never reaches the candidate output PCs. Thus this
high read count is a stationary lookup loop, not a changing waveform.

The links themselves remain photo candidates with pad gaps. The upper
slice's other control bits, chip enable, clock phases, carry wiring, D-input
route, ROM gate and DAC path are not established. The split-slice model is
therefore a configurable diagnostic, not a recovered Nokia datapath or a G2
transmitter/receiver demonstration.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/split_slice_probe.py
```
