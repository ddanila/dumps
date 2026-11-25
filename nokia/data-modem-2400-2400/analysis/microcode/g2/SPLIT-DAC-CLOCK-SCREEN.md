# The D4-dependent loop does not generate carrier samples at two latch clocks

The [D-lane screen](INDEPENDENT-SLICE-D-LANES.md) found a one-loop-delayed
controller-bit effect at ALU word `39E`. This [digital latch replay](split_dac_clock_screen.py)
tests whether that conditional path could be the transmitter under two
explicit LS273 clock hypotheses: a rising edge at `38E` or at `39E`, with
ALU Y wired directly to the latch D byte. The proposed upper-slice instruction
and B-address fields, controller D4 route, clock decode and Y-to-latch bit
order are all **assumptions**. The only photographed DAC data-bit candidate
used here is DAC08 B5←LS273 Q4; its source at the LS273 D4 pin is untraced.

The real 8031 scrambler's 128 bits are each held for eight D38E visits,
matching the 9600 samples/s per 1200 bit/s cadence being tested. Two controls
hold all 128 bits at zero or one. Every run executes 1,024 D38E visits and
1,024 captures at either proposed clock word.

| Clock hypothesis | Steady zero/one latch codes | Photo-candidate B5, zero/one | Actual-stream transitions |
| --- | --- | --- | ---: |
| Rising edge at `38E` | `FB` / `EB` | 1 / 0 | 71 |
| Rising edge at `39E` | `1B` / `3B` | 1 / 1 | 72, including startup |

After the first input, all 1,023 complete 12-word **PC/Y** loop blocks are
identical under constant zero input; the same is true under constant one input. The
two proposed clocks therefore capture a **constant code during each constant
symbol**, not samples of an 1800 Hz carrier. Under the `39E` clock, the one
photo-supported DAC bit B5 does not even carry the controller-bit difference
with the tested Y-bit-to-latch order. The `38E` clock does carry it on B5,
but still yields one constant level per symbol. Both clock hypotheses fail
the C2 transmitter sample criterion in this fixture.

This rejects these two **direct Y→LS273 clock scenarios**, not the physical
modem. Another latch data source, clock decode, input bus lane, instruction
mapping, or controller state may reach the actual line-output computation.
The bits come from a local 8031 scrambler run, not a full data-mode command
frame.
The [report](results/split-dac-clock-screen.json) records the complete
12-word control patterns, capture counts, code sets, B5 values, transition
counts, trace digests and source hashes.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/split_dac_clock_screen.py
```
