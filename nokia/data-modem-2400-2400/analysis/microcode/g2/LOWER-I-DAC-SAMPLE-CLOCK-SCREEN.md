# Direct divided-latch continuations do not produce the 1,800 Hz carrier

The [clock-matched D0 witness](LOWER-I-TIMED-D0-STREAM.md) carries an entire
128-bit controller stream into repeated `3F7` ROM reads and `3F8–3FA`
arithmetic under a candidate 14.4 MHz, eight-microcycle loop. At a 9,600 Hz
DAC sample rate, one sample would be taken every **187.5 loop visits**.
The [digital latch screen](lower_i_dac_sample_clock_screen.py) asks whether
the simplest photo-compatible continuation works: a divided rising clock
captures one internal byte into the adjacent 74LS273, whose output is
tentatively presented to the photographed DAC08HP.

The screen executes the real PROMs and Am27S31 with D3F8 held at `08` or
`09`, the two levels of the successful single-bit candidate route. It tries
four data bytes separately: Am2901 Y at `3F8`, `3F9` or `3FA`, and R10 after
the `3F7` ROM read. For each source it tests all **188 integer sample-clock
phases** in a 187/188-visit cadence. The 74LS273 model captures 32 codes
after a 750-visit warmup. An identity source-byte-to-D-pin route is a
diagnostic full-byte hypothesis; the actual byte wiring is untraced.

| Candidate latch data | Held `08` sampled period | Held `09` sampled period | Phases with 1,800 Hz full-byte peak under both levels |
| --- | ---: | ---: | ---: |
| `3F8` Y | 4 samples | 8 samples | 0 / 188 |
| `3F9` Y | 4 samples | 8 samples | 0 / 188 |
| `3FA` Y | 4 samples | 8 samples | 0 / 188 |
| `3F7` R10 | 4 samples | 8 samples | 0 / 188 |

These periods hold for **every** tested phase. With 32 samples at 9,600 Hz,
1,800 Hz is DFT bin 6; periods of 4 or 8 samples have energy only in bins
that are multiples of 8 or 4, respectively. The 1,800 Hz fraction is zero
within numerical precision for every source and phase. None of the eight
possible Y/R10 source bits fed to candidate 74LS273 D4 yields a B5 1,800 Hz
peak under both held levels either. This B5 calculation uses the
[photo-derived DAC08 B5←74LS273 Q4 segment](DAC08-OUTPUT.md), while the
source-to-D4 route remains a sweep of untraced alternatives.

The [report](results/lower-i-dac-sample-clock-screen.json) records sample
periods, peak frequencies, photo-bit alternatives, phase-zero code examples,
trace digests and source hashes. This excludes **these direct internal-byte
and divided-clock fixtures** as the 1,800 Hz transmitter output. It does
not exclude a 74LS373 hold stage, another instruction or register source,
different sample clock, changed field mapping, or a separate output path.
No physical latch clock or complete DAC data bus has been traced, and no
analog line signal was measured.
