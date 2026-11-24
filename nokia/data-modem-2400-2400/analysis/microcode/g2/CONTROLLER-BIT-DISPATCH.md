# Controller bits through the recurring 38E–38F dispatch

This experiment connects two executed programs under a labelled candidate
interface. The unchanged 8031 ROM computes a scrambled byte stream; the real
DSC2847 control PROMs then receive its bits on the external D input at word
38E. The q3 A/B-swapped mapping is compatible with the three candidate
photo traces in [PHOTO-FIELDS](PHOTO-FIELDS.md). **The route from USART 01 to
D38E, one bit per microcode visit, is a hypothesis, not a traced net or measured
clock relation.**

[`controller_bit_dispatch.py`](controller_bit_dispatch.py) executes the 8031
scrambler routine locally once per byte, feeding each resulting 23-bit history
into the next call. With delay 18, initial history `654321`, and 16 zero input
bytes, the controller ROM yields:

```
38 69 86 38 2D A1 28 12 F2 5C C1 0A AB 4B 29 FB
```

Each byte agrees with the independently verified LSB-first bit recurrence.
The resulting 128 bits are supplied in that order to D at 38E in **one
1,580-instruction DSC2847 run**. The phase-32 quarter-sine fixture and
diagnostic two-bit ROM gate from [the previous loop study](SWAPPED-ROM-LOOPS.md)
are otherwise retained. All 128 D values are consumed at 38E. Word 38F
dispatches to 392 for bit 0 and 396 for bit 1, exactly matching the input
sequence. Both four-word entries yield the same ALU Y quartet,
**0, 0, 190, 64**, on every visit. An all-zero-bit control takes a different
control-flow trace but yields the identical 128 quartets. Thus the controller
bits affect control flow in this candidate path without modulating its
candidate output.

First-pass values 0, 1, 2 and 3 select 392, 396, 39A and 39E respectively.
At phase 32, values 0 and 1 repeat their equal quartets 81 times in a
1,020-instruction fixture. Values 2 and 3 produce a zero quartet once and
then reach 084. A separate sweep of **all 65 quarter-sine phase fixtures**
finds equal output quartets for values 0 and 1 at every phase. This makes a
direct interpretation of 38E as a two-bit DPSK symbol input unsupported by
these runs; another mapping, startup state or output connection could behave
differently.

The [report and full controller-driven microcode trace](results/controller-bit-dispatch/report.json)
retain the ROM hashes, input bits, every dispatch and output quartet, the
all-zero control, the four-way check, all 65 phase comparisons and source
hashes. The controller routine is entered locally for each byte and its
history is passed between calls; the 8031 main loop and physical USART TxD
pin are not yet co-simulated. The ALU Y quartet has not been traced to the
DAC. This is a discriminating C2 candidate test, not a passing transmitter
or receiver/echo test.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/controller_bit_dispatch.py
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode/g2 -p 'test_controller_bit_dispatch.py' -v
```
