# A free-running latch clock also carries the joint-map transmitter signal

The [joint-map PROM-edge replay](JOINT-MASK04-TX-PROM-EDGE.md) captures
one candidate DAC sample per 375 U10 D2 edges. That divider has not been
found on the board. This [alternative](joint_mask04_free_clock_msb.py)
uses a free-running latch clock every 1,500 microinstructions and tests
all four instruction phases `127`–`12A` in the same uninterrupted
controller-derived A1 tone → A2 → A3 `FF` reversals → A4 data streams.
Each call/answer run executes **1,248,256 real-PROM instructions** on the
fixed lower-mask-`04` joint map and captures 832 samples at every phase.
Both trace digests match the prior joint-map transmitter and PROM-edge
runs. The `128` and `129` samples also match the corresponding prior
edge-capture hashes.

The script applies the same six photo-compatible DAC bus orders, assumed
1,950 Hz Q=1 bandpass and independent known-carrier decoder. Every bus
order maps Am2901 Y7 to DAC code bit 7, the candidate DAC08 B1/MSB.

| Free-clock capture phase | Full-code A1 peak | Full-code A3/A4 errors | MSB-only A1 peak | MSB-only A3/A4 errors | Lower-seven-bit errors |
| --- | ---: | ---: | ---: | ---: | ---: |
| `127` | 2,100 Hz | 0/62 | 2,100 Hz | 0/62 | 22–23/62 |
| `128` | 2,100 Hz | 0/62 | 2,100 Hz | 0/62 | 22–23/62 |
| `129` | 2,100 Hz | 0/62 | 2,100 Hz | 0/62 | 22–23/62 |
| `12A` | 2,100 Hz | 0/62 | 2,100 Hz | 0/62 | 21–24/62 |

Each error range covers both controller selectors and all six bus orders;
these repeated buses share the same MSB source. The four raw sample
streams have distinct SHA-256 hashes in each selector mode, despite
identical tone peaks and decision scores. Thus these output metrics do
not choose a physical latch phase. They do show that a periodic sample
clock can reproduce the tested behavior without a `129`-qualified
375-edge PROM counter. If one microinstruction lasts one period of the
photographed 14.4 MHz oscillator, 1,500 instructions per capture imply
9,600 samples/s; that timing and the clock connection are assumptions.

This is another **conditional C2 route**, not a line-output measurement
or a C2 pass. Y7-to-latch, latch-to-DAC08 B1/pin 5, the other DAC bits,
A2 hold/mute control, current-output conversion, analog filter and line
connector remain untraced. The one photo-suggested DAC data segment is
74LS273 Q4→DAC08 B5, which does not by itself carry the 2,100 Hz tone.
Next discriminate the sample phase by a photo-compatible latch-clock or
analog-output constraint; a tone peak and reference dibits alone cannot
pick it. Missing continuity does not stop those candidate tests.

The [machine report](results/joint-mask04-free-clock-msb.json) saves the
phase-specific hashes and all bus/selector scores. Reproduce from the
microcode directory with `python3 g2/joint_mask04_free_clock_msb.py`.
