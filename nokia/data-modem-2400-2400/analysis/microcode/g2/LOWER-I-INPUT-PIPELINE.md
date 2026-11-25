# Two lower instruction sources extend an input transient through four loops

The translated split-slice mapping assigns **U11 bit 6 to both U2 I2 and
I7**. The [source screen](lower_i_input_pipeline.py) tests all eight direct
U11 bits at each of those two instruction inputs under the existing
separated-slice, upper-B hypothesis. U11→U6 is suggested by the board
layout; the individual U6→U2 instruction nets are untraced. Every run uses
the real control PROMs and Am27S31 dump, Q=5, zero RAM, and a hypothesized
controller bit on D4 at `38E`.

All 16 source choices reach and select 128 D38E inputs. Each still changes
candidate `39E` ALU Y **once**, one visit after a single D4 pulse. The
lower U11.6 fan-out is therefore *not required* for that one-visit relay;
the separate U18.6 upper-field dependency remains as described in the
[upper-field screen](UPPER-I-FIELD-SENSITIVITY.md).

U2 I2 from **U11 bit 0 or bit 4** produces a longer internal effect. Pulses
at input visits 20, 40 and 80 each change the full modeled RAM/Q/flag/stack
checkpoint at that visit and the next **three** visits, then reconverge.
The original U11.6 assignment changes only the current and next checkpoint.
No pulse changes a selected ROM **address** in these three cases.

With the executed 128-bit 8031 scrambler stream, both U11.0 and U11.4
variants have exact one-bit lag rules after startup: `389`, `38A`, `38C`,
`39E` and `3A0` reflect the previous input bit; `38F` and `3A1` reflect the
bit from **two** visits earlier. For example, under U11.0 the `3A1` ALU Y
is `60` for a two-visit-old zero and `44` for a one, at every checked visit
after the first eight. The original U11.6 mapping has no input-dependent
`38F` or `3A1` ALU Y in that interval.

This is a short modeled data pipeline, not demonstrated pulse shaping,
receiver decoding, or a DAC-bound sample stream. The output candidate still
gets one delayed bit-dependent level and no carrier waveform. The
[report](results/lower-i-input-pipeline.json) retains all source choices,
three pulse positions, lag rules, trace digests and source hashes. The result
identifies U2 I2 as a useful pin to constrain while continuing to search for
a retained ROM-using or output path.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/lower_i_input_pipeline.py
```
