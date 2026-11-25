# The candidate A2 latch gate stays low for about 594–596 DAC samples

The [A2 frame-bit screen](CONTROLLER-A2-LATCH-GATE.md) found one held CD4094
frame bit that is high in A1/A3/A4 and low in A2. This
[instruction-level probe](controller_a2_latch_gate_timing.py) times its
changes at the controller's P1.2 frame-latch pulse, after the fourth SBUF
byte, in the same interrupt-paced 8031 run.

| Selector | A2 frame-latch fall, third byte | A3 frame-latch rise, third byte | Low interval | Candidate DAC samples |
| --- | --- | --- | ---: | ---: |
| `40` | tick 2,616,560; `C1→E8` | tick 2,678,498; `88→A1` | 61,938 ticks | 595.56 |
| `60` | tick 2,616,376; `C1→E8` | tick 2,678,148; `88→A1` | 61,772 ticks | 593.96 |

The sample conversion uses two explicit clock hypotheses: the photographed
11.9808 MHz controller oscillator with a classic 12-clock 8031 gives
998,400 machine ticks/s, and the DSC's 14.4 MHz oscillator divided by 1,500
gives 9,600 candidate DAC samples/s. Their ratio is exactly **104 controller
ticks per DAC sample**. Thus the proposed 74LS373 enable would hold its
output for roughly 594–596 sample periods. The earlier DAC hold screen
covered only 64 A2 samples.

The P1.2 latch pulse is itself modeled with an eight-tick synthetic SBUF
completion; CD4094 shift/latch propagation and the bit-to-74LS373 route are
untraced. These are executed controller event times under a labelled fixture,
not measured hardware timing. The [extended real-PROM replay](JOINT-MASK04-A2-LE-TIMED.md)
uses this interval to test the candidate output behavior. The
[machine report](results/controller-a2-latch-gate-timing.json) records the
events and source hashes. Reproduce from the microcode directory with
`python3 g2/controller_a2_latch_gate_timing.py`.
