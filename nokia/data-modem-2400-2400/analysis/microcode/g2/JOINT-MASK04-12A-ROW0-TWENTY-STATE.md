# Revised row-output phase gates recover new payloads across gain

The [frozen 14-state gate rule](JOINT-MASK04-12A-ROW0-GAIN-CHALLENGE.md)
failed on new 75%-level state `52`. I moved those six gain runs into
development, as promised before refitting. The resulting 22
real-PROM receive cases form one connected, zero-conflict graph of 20
observed seven-bit phase states. Minimizing the two phase outputs
separately gives a small revision. With `s2` = first `3F8` Y7, `s3`
= second `3F8` Y7, `s4` = second Y4 and `s6` = `3ED` row-0 bit 0 at
visit 46:

```text
p0 = (!s2 & !s4 & !s6) | (!s2 & !s3) | (s2 & s3 & s6)
p1 = !s6 | !s2
phase = p0 + 2*p1
dibit = inverse(phase_now - phase_previous mod 4)
```

The inverse maps phase steps `2,1,3,0` to dibits `0,1,2,3`. The
new `!s2 & !s3` term repairs the observed low-level state without
changing phase bit 1. The fit itself is development evidence.

I froze this 20-state gate rule before offering a seventh, previously
unused eight-byte payload per selector. At diagnostic R1 offset 88,
the real q3/mask-04 PROM transmitter and receiver ran at 75%, 100%
and 125% of the same fixed line gain:

| Selector | Fresh source payload | Levels with 64/64 exact decisions and eight line bytes | Aligned modeled 8251/8031 |
| --- | --- | --- | --- |
| `40` | `62 E5 19 A7 D0 3B 8F 54` | 75%, 100%, 125% | eight exact bytes, zero errors/overruns at each level |
| `60` | `9C 41 F6 28 B3 0D 75 EA` | 75%, 100%, 125% | eight exact bytes, zero errors/overruns at each level |

Both source streams exercise all four payload dibits. The independent
reference decoder is exact in all six cases. Only the aligned external
SYNDET pulse recovers the source payload; one-bit-early and one-bit-late
pulses fail in every case. The older six-bit lookup leaves 55–64 of
the 64 decisions unknown in these runs and makes two known-key errors
at 75% in each selector.

Every state reached by this holdout was already among the 20
development states. This is a clean new-**data** and gain validation
at another carrier start, not a test of a further unseen state. The
gate expression is an external logic hypothesis; it does not prove
that Nokia wired `3ED` row 0 into a latch or that the modeled
RxD/RxC/SYNDET path exists.

The [20-state fit](results/joint-mask04-12a-row0-boolean-twenty.json),
[real-PROM holdout](results/joint-mask04-12a-row0-boolean-twenty-fresh-88.json)
and [audit](results/joint-mask04-12a-row0-boolean-twenty-audit.json)
contain phase states, traces, line decisions, controller handoffs and
source hashes. Reproduce with:

```sh
python3 g2/joint_mask04_12a_row0_boolean_twenty.py
python3 g2/joint_mask04_12a_row0_boolean_twenty_fresh.py
python3 g2/joint_mask04_12a_row0_boolean_twenty_audit.py
```

C3/G2 remain open. Next test the frozen gates at carrier/frequency
drift or another unseen-state condition, and model a photo-compatible
row-output latch and serial route. An assumed wire is sufficient to
run the test; it remains conditional until independently constrained.
