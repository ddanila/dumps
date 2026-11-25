# An eight-visit one-pin stream survives the ROM loop

The [reproducible screen](lower_i_four_sample_bit_screen.py) ran every ordered
pair of the ten individually live D3F8 low nibbles with each of 128 locally
ROM-executed 8031 scrambler bits held for four or eight visits to D3F8. It
used the same real-PROM, upper-bank, Q=`05`, zero-RAM, candidate-split-slice
fixture as the [earlier bridge](LOWER-I-NIBBLE-STREAM-BRIDGE.md). The
[JSON report](results/lower-i-four-sample-bit-screen.json) contains all 180
cases and the surviving trace comparison.

No four-visit pair consumed all 512 offered D3F8 values. At eight visits,
exactly one of 90 pairs consumed all 1,024 values: bit 0=`08`, bit 1=`09`.
Its D0-only change is a simple conditional controller-input hypothesis. All
1,024 input reads selected the offered values; the run made 1,157 D3F8 and
3F7 visits. The selected 3F7 ROM address had 30 distinct values and differed
from the constant-zero control on 977 of the first 1,024 visits. ALU Y at
3F8, 3F9 and 3FA had 16, 16 and 15 distinct values. This is a repeatable
internal controller-dependent path, not a known DAC08 byte stream.

If eight loop visits represent one 2,400 bit/s bit, this eight-microcycle loop
would run at 19,200 visits/s; a 9,600 sample/s latch could clock every two
visits. That implies a 153.6 kHz microcycle, a clock ratio **not measured on
the board**. The next runnable test is to clock candidate latch bytes from
each of those sites on alternating visits, then compare steady-symbol and
controller-stream spectra and phase. If the direct sources fail, vary the
untraced latch data route or clock phase. No missing pin trace blocks that
test, and the transmitter acceptance criteria remain unchanged.
