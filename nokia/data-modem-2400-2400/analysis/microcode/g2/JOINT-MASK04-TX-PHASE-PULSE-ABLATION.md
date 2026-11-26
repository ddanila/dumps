# One controller dibit causes the predicted persistent R1 phase change

The [full-A4 replay](joint_mask04_tx_phase_pulse_ablation.py) extends the
earlier [18-dibit phase-accumulator check](JOINT-MASK04-TX-PHASE-ACCUMULATOR.md)
to **all 32 data dibits** from each real 8031/8251 controller stream.
The executed q3/mask-04 PROM loop accepts the same labelled D127
four-visit pulse route. Each normal run executes 384,256 PROM words;
each paired control changes only dibit 23 (zero-based) from `11` to
`00` in the offered pulse stream. The script checks that exactly four
D127 visits, 69,000–69,003, differ between each pair.

| Selector | `127` visits per run | Checked R1 additions per run | Checked Y7/R1-high relations per run | Post-intervention symbol-end phase difference |
| --- | ---: | ---: | ---: | ---: |
| Call `40` | 96,054 | 96,053 | 384,216 | 128/256 |
| Answer `60` | 96,054 | 96,053 | 384,216 | 128/256 |

At each `127` visit after the first, executed R1 equals its preceding
value plus the selected D127 byte modulo 256. At all four reached loop
words `127–12A`, Y7 equals R1 bit 7. The controller-derived dibit `11`
uses `90` for four visits; its ablated `00` control uses baseline `B0`.
The control therefore adds `4×(B0−90) = 128` phase counts relative to
the normal stream. Every symbol end before dibit 23 matches exactly;
dibit 23 and all eight later symbol ends differ by 128 counts in both
selectors. The sampled Y7 hashes and complete PROM trace digests also
change, while loop visit and arithmetic-check counts stay equal.

This is an executed, causal explanation for how the candidate transmit
carrier responds to a controller dibit under the explicit D127 input
fixture. A 128-count phase step reverses the high-bit waveform after
the pulse; it matches the candidate V.26 ter differential half-turn.
The controller-to-D127 pulse decoder, sample clock, Y7 latch input,
DAC08 code wiring and analog line output are still assumed or
untraced. Thus the result strengthens the internal transmitter
mechanism but does not by itself pass C2 or identify a measured line.

The [machine report](results/joint-mask04-tx-phase-pulse-ablation.json)
retains both 32-dibit streams, every symbol-end phase and offset, the
ablation differences, trace and sampled-bit hashes, and source hashes.
Reproduce from the microcode directory:

```sh
python3 g2/joint_mask04_tx_phase_pulse_ablation.py
```
