# A phase-step candidate reaches the photo-supported DAC B5 bit under a latch hypothesis

The [D127 ROM walk](PHOTO-127-LIVENESS.md) advances a PC129 address by a held
byte under a Q=0, held-I0 mapping hypothesis. The selected Am27S31 byte
affects `Y129` but is overwritten before the next loop. An external latch
sampling that transient Y is therefore a concrete output-path candidate.
The [DED 3558 photo review](DAC08-OUTPUT.md) suggests DAC08 B5 is connected
to nearby 74LS273 Q4; the segment is not continuity-verified. The
[bit replay](photo_dac_b5_tone_step.py) clocks a digital LS273 once at each
PC129 and tests all eight possible Y bits as its D4 source. That Y→D4 route,
clock and 9,600 samples/s cadence are assumptions.

Eighteen real-PROM runs test nine held D127 increments (`16–80` in steps of
8) with the PC129 ROM operand in the lower or upper bank. Each run supplies
128 captures, and the runner checks the selected-read and four-cycle PC129
cadence. For the **upper-bank, Y7→D4** candidate, the resulting B5 sequence
has its strongest DFT bin at `increment × 9600 / 256` Hz for **all nine**
increments. The target values and nearby controls are:

| D127 | Target under assumed rate | Upper-bank B5 peak | Target-bin variance fraction | Lower-bank B5 peak |
| ---: | ---: | ---: | ---: | ---: |
| 40 | 1,500 Hz | 1,500 Hz | 0.486 | 1,500 Hz |
| **48** | **1,800 Hz** | **1,800 Hz** | **0.661** | 3,600 Hz |
| **56** | **2,100 Hz** | **2,100 Hz** | **0.486** | 2,100 Hz |
| 64 | 2,400 Hz | 2,400 Hz | 1.000 | 2,400 Hz |

For upper-bank increments 48 and 56, **Y7 is the only one** of the eight
tested Y-bit-to-D4 choices whose B5 peak lands at the corresponding target.
The ordinary same-position Y4→D4 assumption does not. The upper-bank 48
result also separates this candidate from the lower-bank Y7 run, whose
strongest bin is the second harmonic. Those are useful constraints on a
possible byte/bit route, not a measured pin connection.

The [machine report](results/photo-dac-b5-tone-step.json) includes all
18×8 bit choices, spectra, transition counts, ROM addresses, trace digests
and source/photo hashes. Because every tested upper-bank increment produces
its own step-frequency peak, the 1,800 and 2,100 Hz cases **do not identify
which D127 values Nokia uses**. A single DAC input bit does not establish
the full output code or analog line waveform. The D127 source, A8 driver,
held-I0 circuit and LS273 clock remain untraced; the [raw clock screen](PHOTO-127-CLOCK-SCREEN.md)
shows that unqualified PROM-bit edges at PC129 run far faster than the
assumed sample cadence under the fast-clock hypothesis. No controller tone
command, data modulation or receive/echo path is shown by this test.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/photo_dac_b5_tone_step.py
```
