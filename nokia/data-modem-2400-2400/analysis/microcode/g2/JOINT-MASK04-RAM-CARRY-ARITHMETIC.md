# The sustained RAM route feeds `3FA` a delayed code, not a varying R10 estimate

The [word-level audit](joint_mask04_ram_carry_arithmetic.py) replays the
four own-echo, remote, mixed and zero inputs from the
[previous-carry feedback screen](JOINT-MASK04-RAM-CARRY-ECHO-SCREEN.md).
Each run executes 288,047 real-PROM words and sustains 9,000 ADC visits.
The audit traces the first 6,000 `3FA` words per run, covering all 128
training samples, and checks **24,000 split-slice arithmetic equations**
against the actual selected RAM-return D byte, pre-word R10/R13, carry,
ALU F/Y and conditional R13 write.

At `3FA` the executed low/high instructions are `55/C5` with A=R10,
B=R13. The checked equation is:

```text
low_total = Dlo + ~R10lo + carry
Ylo       = low_total & 15
Yhi       = (Dhi + R10hi + (low_total >> 4)) & 15
R13hi     = Yhi
```

The hypothetical RAM read forces D's low nibble to `1`. At **every one**
of the 24,000 training `3FA` reads, pre-word R10 is `10`; hence its low
nibble is zero, the low-slice carry-out is one, and this site simplifies
to `Yhi=(Dhi+2)&15`, `Ylo=carry_in`. The changing high output is therefore
explained by the delayed RAM-return high nibble, while the low bit is the
current carry input. The observed training counts are:

| Input | R10 at `3FA` | Carry 0 / 1 | Distinct D bytes | Distinct Y bytes |
| --- | ---: | ---: | ---: | ---: |
| Zero | `10` for 6,000 | 6,000 / 0 | 2 | 2 |
| Own echo | `10` for 6,000 | 6,000 / 0 | 3 | 3 |
| Remote | `10` for 6,000 | 4,685 / 1,315 | 4 | 7 |
| Remote + echo | `10` for 6,000 | 4,309 / 1,691 | 5 | 9 |

R10 is **not globally constant**: the full trace records thousands of
R10 changes elsewhere in each receive loop. The narrower result is that
R10 returns to `10` before every tested `3FA` calculation; it contributes
no changing echo estimate at this proposed output site. R13 also changes,
but this instruction uses R13 as its write destination, not its A input.
An untraced consumer of another word or a different controller mode could
behave differently.

This arithmetic explains the previous screen's growing `3FA` code-space
contrast without promoting those unsigned bytes to an analog residual.
It also narrows the next C4 test: seek a mode or feedback timing that
makes a trained state enter the actual `3FA` operand, or inspect a
different executed output. The photographed RAM and TEST connections
remain hypotheses. C4 and G2 stay open and active.

The [machine report](results/joint-mask04-ram-carry-arithmetic.json)
contains all four trace/input hashes, checked equation counts and
early/late/whole-training operand distributions. Reproduce from this
directory with `python3 g2/joint_mask04_ram_carry_arithmetic.py`.
