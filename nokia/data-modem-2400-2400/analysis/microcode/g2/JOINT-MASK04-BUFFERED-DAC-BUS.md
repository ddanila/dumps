# Full DAC byte candidates on buffered real-PROM streams

The buffered serial-to-`D127` handoff previously used only one hypothetical
DAC input bit. This screen asks whether a complete 8-bit DAC08 code remains
credible when the visible 74LS273 Q4→DAC08 B5 segment is honored. It freezes
the 12 bus permutations that decoded the earlier controller streams with
zero errors, then applies them to actual Am2901 Y bytes captured from the
full call and answer A1–A4 runs. Ordered Y→74LS273 D bits, the other seven
Q→DAC08 B wires and the sample clock remain explicit assumptions.

Each selector executes 1,269,256 real DSC PROM instructions. The script
captures 846 complete Y bytes at both `127` and `129` on the proposed
9,600-sample/s cadence. The `127` Y7 stream must hash-match the saved
[buffered handoff](JOINT-MASK04-BUFFERED-SERIAL-HANDOFF.md). The two capture
sites have different Y-byte and DAC-code hashes, so they are genuinely
different digital candidates. For each bus order, the same assumed A2
mid-code gate and Q=1 line filter feed an independent differential decoder.

| Latch word | Bus orders with 0 errors on both 64-check streams | Other orders | A1 peak / R² at 2,100 Hz | Largest A2/A1 RMS ratio |
| --- | ---: | --- | --- | ---: |
| `127` | 6 of 12 | one call error at symbol 36; answer exact | 2,100 Hz / 0.927–0.948 | 1.98×10⁻⁸ |
| `129` | 6 of 12 | one call error at symbol 36; answer exact | 2,100 Hz / 0.927–0.948 | 1.25×10⁻⁸ |

The six common survivors are precisely the frozen permutations that assign
Y bit 6 to DAC code bit 5, while all 12 assign Y bit 4 to DAC B5 and Y bit
7 to the DAC MSB. Each candidate emits 32 distinct DAC codes in each
complete run. This supports a **conditional full-byte** transmitter path
through A1 tone, A2 silence, A3 training and A4 data, rather than only a
single-bit carrier. It does not identify a unique bus order, select `127`
versus `129`, prove the assumed A2 gate or measure the analog output.

The photo-suggested Q4→B5 trace is only one segment. Y→D order, seven Q→B
wires, latch clock, DAC08 current-output stage, line filter and actual line
connector remain untraced. C2 stays open. A useful next discriminator is a
second visible DAC bit or a timing/output-node constraint; the surviving
orders can be carried into receiver tests without calling them board facts.

Run `python3 g2/joint_mask04_buffered_dac_bus.py` from the microcode
directory. The [machine report](results/joint-mask04-buffered-dac-bus.json)
records the frozen permutations, PROM trace and sample hashes, tone/silence
metrics and every decoded symbol error.
