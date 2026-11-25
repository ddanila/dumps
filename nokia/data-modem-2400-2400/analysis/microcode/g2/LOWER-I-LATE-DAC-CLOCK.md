# Direct clocks in the late loop do not give an 1800 Hz reference carrier

The [late-byte relay](LOWER-I-LATE-BYTE-RELAY.md) gives a repeated quartet of
internal Y values at `3B3–3B6`. The photographed DAC08 B5←74LS273 Q4
segment is one possible downstream data bit, but the LS273 D input and clock
are untraced. This [digital latch replay](lower_i_late_dac_clock.py) tests a
rising LS273 clock at each nonempty fixed subset of those four words (15
clock sets). It also tests all eight Y-bit candidates for LS273 D4, so the
photo-supported B5 segment can be evaluated without assuming a particular
Y-to-D bit order. Full-byte Y→LS273 D is a separate, explicit hypothesis.

The runs use the same real-PROM mapping, previous-carry condition candidate,
Q=5 and D3F8 trigger as the relay experiment. They offer constant zero,
constant one and the real 128-bit 8031 stream on D1 of the untraced D3A6
source. Each 2,000-cycle run reaches 138 loop quartets; the controller run
checks all 128 bits before holding the last input value.

The larger `3A2–3B6` loop contains 12 words. For each constant-symbol
control, the runner compares every one of **137 complete PC/Y blocks** after
the first `3A2`: all 137 are identical. Thus a rising edge at any fixed
nonempty subset of those 12 words would repeat at most 12 captured values
per loop. The 15 four-word clock sets are executed explicitly below; the
12-word invariant covers the other fixed-site choices without pretending
to know which word, if any, drives the physical latch clock.

Under either constant input, every output quartet repeats exactly. A clock
at one of the four words therefore captures one constant code per loop. A
clock at multiple fixed words captures the same short code pattern on every
loop: its fundamental period is at most four samples. The same bound holds
for B5 under all eight Y-bit-to-LS273-D4 choices. For example, with an edge
at all four words, the direct Y-byte candidates are:

| D3A6 byte | Repeated `3B3,3B4,3B5,3B6` codes |
| --- | --- |
| `01` | `F1 F2 01 0E` |
| `03` | `F3 F4 03 0C` |

At the plan's **hypothetical 9,600 samples/s**, an 1,800 Hz carrier has a
3/16-cycle phase advance per sample. A sequence whose period divides four
cannot contain that discrete frequency. Thus none of these direct, fixed
`3B3–3B6` clock choices supplies the required constant-symbol carrier at
that cadence, even if an untraced static byte wiring permutes the values.
The same 16-sample-period requirement excludes every fixed clock subset
of the whole 12-word loop under this direct-edge model.
The [machine report](results/lower-i-late-dac-clock.json) records all 15
clock sets, constant-code and B5 periods, controller-stream code counts,
trace digests and source/photo hashes.

This does **not** determine the board clock, the other DAC input pins, the
LS373 hold behavior or the analog output. A different sample rate, a hold
stage, a clock on another program path or a data source outside this loop may
change the result. The quartet remains a real executed arithmetic relay
under stated hypotheses, not a demonstrated line-output waveform.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/lower_i_late_dac_clock.py
```
