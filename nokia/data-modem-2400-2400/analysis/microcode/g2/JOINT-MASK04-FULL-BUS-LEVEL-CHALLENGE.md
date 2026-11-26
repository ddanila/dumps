# Full-byte joined readout fails a modest ADC-level change

The [non-zero full-byte holdout](JOINT-MASK04-FULL-BUS-PAYLOAD-HOLDOUT.md)
showed exact data recovery at the nominal modeled ADC level. This
challenge keeps the same frozen DAC order `[4,0,6,1,3,2,5,7]`, `127`
latch word, zero-run controller streams, filter, ADC cadence, receiver
tables and fixed-first fallback. It first reruns the real DSC transmitter
and requires its complete Y-byte and nominal PCM hashes to match the
saved [full-byte loopback](JOINT-MASK04-BUFFERED-FULL-BUS-LOOPBACK.md).
Only the receiver input changes: scale nominal PCM by 0.75 and add
either +16 or −16 counts before the hypothetical complementary ADC.
Each variant executes 780,047 real-PROM receive instructions.

| Selector | PCM bias | Reference wrong | Frozen 46/93 wrong / unknown data dibits | Margin wrong / unknown | Fixed-first wrong / unknown |
| --- | ---: | ---: | ---: | ---: | ---: |
| `40` call | +16 | 0 | 0 / 17 | 5 / 3 | 3 / 3 |
| `40` call | −16 | 0 | 6 / 14 | 2 / 9 | 6 / 9 |
| `60` answer | +16 | 0 | 0 / 21 | 5 / 6 | 4 / 6 |
| `60` answer | −16 | 0 | 8 / 15 | 5 / 8 | 8 / 8 |

No PCM sample clips. The independent known-carrier reference decoder
still recovers every modeled dibit, so the signal contains the data;
the present executed-byte readout does not recover it under these level
changes. None of the four variants yields all eight controller line
bytes, and no unknown decision is filled from the expected stream.
This limits the nominal and non-zero holdout successes to their stated
ADC-level fixture.

Gain and bias are modeled analog/ADC choices, not measured Nokia board
conditions. The board may normalize its input, track midpoint or use a
different decision circuit. The earlier [state-level probe](JOINT-MASK04-RX-STATE-LEVEL-PROBE.md)
found R0/R1/R12/Q responsive to a changed input but no identified gain
estimate; a fixed Boolean alternative also failed on the joined stream.
Inspect executed state at additional visits or a photo-compatible AGC and
decision path, freeze any adaptive rule, and challenge it on fresh data
and phase cases. C3 and G2 remain open and active.

Run `python3 g2/joint_mask04_full_bus_level_challenge.py` from the
microcode directory. The [machine report](results/joint-mask04-full-bus-level-challenge.json)
records source hashes, PROM trace digests, ADC hashes and all frozen
decision scores.
