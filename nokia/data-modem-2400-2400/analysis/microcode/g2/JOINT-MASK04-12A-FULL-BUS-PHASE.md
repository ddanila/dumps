# The executed `12A` byte has tone, reversal and data-phase signatures

The [full-byte phase replay](joint_mask04_12a_full_bus_phase.py) reruns the
unchanged q3/mask-`04` real-PROM transmitter for both controller selectors
on the buffered eight-zero-byte fixture. The trace and 846-sample `12A` Y
hashes match the earlier [buffered line run](JOINT-MASK04-12A-BUFFERED-LINE.md).
Each 375th `12A` Y byte is mapped through all six surviving
photo-compatible DAC08 bus orders. No bus order is selected using this test.

| Candidate observation | Call `40` | Answer `60` |
| --- | --- | --- |
| Raw full-byte A1 peak | 2,100 Hz on all six buses | 2,100 Hz on all six buses |
| Maximum adjacent A1 phase drift at 2,100 Hz | 19.5° | 19.5° |
| A3 segment-1 adjacent phase at 1,800 Hz | ±180° for all 31 transitions on every bus | ±180° for all 31 transitions on every bus |
| A4 raw eight-sample data phasor: worst error from expected dibit step | 48.2–50.4° | 60.5–62.8° |
| A4 after the **previously fixed** Q=0.5 bandpass and +6-sample alignment, using the reference model's matched symbol window: worst step error | 38.1–40.0° | 33.0–35.1° |

The raw eight-sample phasor is too crude for some data transitions: its
errors can exceed the 45° nearest-quadrant boundary. The fixed analog
filter and the reference receiver's nine-symbol raised-cosine window
bring all 32 data steps per selector and bus into the prescribed V.26 ter
quadrants. The phase convention and offered dibits were fixed before this
check; the matched-window calculation uses the same known-carrier reference
model that previously decoded the line, so it is a detailed measurement of
that **conditional** result rather than an independent onboard decoder.

This puts all four requested transmit signatures in one executed `12A`
candidate: the 2,100 Hz tone, 180° segment-1 reversals, and correct
call/answer data phase steps; earlier sustained-carrier tests supply the
1,800 Hz carrier. It still does **not** pass C2. The Y-to-74LS273 data
route, divided latch clock, six unresolved DAC bus orders, DAC08 current
output and analog line connection are untraced. The Q=0.5 filter and A2 mute
are scenario assumptions. A useful next discriminator is an independent
constraint on the DAC08 current output or the 74LS273 clock/data pins;
meanwhile the six bus orders remain runnable hypotheses rather than a G2
blocker.

The [machine report](results/joint-mask04-12a-full-bus-phase.json) saves
all adjacent phase angles, errors, sample hashes and source hashes.
Reproduce from the microcode directory with:

```sh
python3 g2/joint_mask04_12a_full_bus_phase.py
```
