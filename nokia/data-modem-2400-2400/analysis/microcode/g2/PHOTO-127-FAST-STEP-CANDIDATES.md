# Alternative D127 steps can restore candidate tone rates after a fast clock

The [clock-alias screen](PHOTO-127-CLOCK-ALIAS.md) showed that D127=`30/38`
(48/56) no longer gives 1,800/2,100 Hz at the photo-supported DAC B5
candidate if a fast PC129 loop is gated down to 9,600 samples/s. Under the
same held-I0, upper-bank, Y7→LS273-D4 and output-gate hypotheses, the
[candidate runner](photo_127_fast_step_candidates.py) solves for other held
D127 bytes that make the *sampled* phase advance 48 or 56 units per sample.
The physical D127 source, 14.4 MHz divider and DAC clock are still untraced.

For one microinstruction every `k=1` or `k=3` oscillator periods, PC129
is reached once every four microinstructions, giving exactly 375 or 125
PC129 visits per proposed 9,600 Hz output sample. Solving
`D127 × visits_per_sample ≡ ±target_step (mod 256)` gives:

| k | Target | Forward D127 | Reverse D127 |
| ---: | ---: | ---: | ---: |
| 1 | 1,800 Hz (step 48) | `50` | `B0` |
| 1 | 2,100 Hz (step 56) | `88` | `78` |
| 3 | 1,800 Hz (step 48) | `F0` | `10` |
| 3 | 2,100 Hz (step 56) | `98` | `68` |

All eight byte values were run through **3,000 real-PROM microinstructions**
each. Each reaches 740 selected PC129 reads, and every read matches the
phase, Am27S31 upper-bank byte and ALU-Y recurrence. The runner then projects
640 gated B5 samples from that checked recurrence and tests every distinct
start phase (16 or 32 per byte). Every candidate peaks at its intended
frequency. With forward steps and zero start offset, the projected B5 bit
series is byte-for-byte identical to the earlier one-PC129-per-sample
48/56 series. Reverse steps give the same target-bin variance fraction,
0.661 for 1,800 Hz and 0.486 for 2,100 Hz, with opposite phase direction.

For `k=2` or `k=4`, a 9,600 Hz gate must alternate PC129 visit intervals
`187/188` or `93/94`. Since adjacent intervals differ by one visit, no
fixed **nonzero** D127 byte can make the phase advance identical on both
intervals modulo 256. This rules out an *exact uniform* sampled phase step
for that simple gate; it does not exclude a jittered signal or a different
clock circuit.

The lower-bank Am27S31 region `30–7F` happens to contain `F0` at `5D` and
`10` at `66`, the two `k=3` 1,800 Hz alternatives. None of the four
2,100 Hz candidate bytes appears in that region. These are value
co-occurrences, **not evidence that the table drives D127**. No controller
tone command or full DAC output route has been identified. The
[machine report](results/photo-127-fast-step-candidates.json) records all
eight executed traces, start-phase screens, ROM-region hits and source hashes.
This narrows the timing and step-source candidates to test next without
treating the missing connection as a blocker.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/photo_127_fast_step_candidates.py
```
