# What the delayed RAM byte actually does at `3FA`

The [matched-tail RAM pulse](JOINT-MASK04-RAM-PULSE-FREEZE.md)
showed that a hypothetical stored ADC byte can change `3FA` Y three or
sixteen samples later. This [trace check](joint_mask04_ram_return_arithmetic.py)
replays the baseline and pulse at both delays under held `D3EB=01`, and
at three samples under held `A1`. It captures every `3FA` word while
the changed RAM address is read: **47 words per case, 282 checked words**
in six real-PROM executions.

At this address the joint mask-`04` mapping selects low/high Am2901
instructions **`55/C5`**, A=R10, B=R13 and the assumed external RAM D.
The low slice computes `Dlo + ~R10lo + carry_in`, while the high slice
computes `Dhi + R10hi + low_carry`. Y is their combined F byte. The
low slice does **not** write its result; the high slice writes only the
high nibble of R13. This is a mixed split-slice operation, **not** a
full-byte `D − R10` subtraction.

| Held `D3EB`, lag | RAM D baseline→pulse | Pre-word R10 | Input carry | F/Y baseline→pulse | Post-word R13, both |
| --- | --- | --- | ---: | --- | --- |
| `01`, 3 samples | `01→0F` | `10` | 0 | `20→2E` | `20` |
| `01`, 16 samples | `01→0F` | `10` | 0 | `20→2E` | `20` |
| `A1`, 3 samples | `01→0F` | `20` | 0 | `30→3E` | `30` |

Every row in each 47-word window satisfies the split equation against
the reconstructed **pre-word** R10 and the selected external D. The
baseline and pulse have the same pre-word R10, pre-word R13, carry and
Q at matched cycles. They also write the same post-word R13. At the
sixteen-sample lag, pre-word R13 takes `50` or `60` within the window,
but the same values occur at each corresponding baseline/pulse cycle.
The RAM byte changes Y's low nibble without retaining that difference
in this word's modeled Q/RAM destination; this explains why the
delayed impulse lasts only while that RAM address is read.

The candidate RAM pins, address clock, write gate, D return, mode lane
and Y consumer are still assumptions. This arithmetic alone neither
identifies an echo residual nor proves receive-bit computation. In the
corrected [own/remote/mixed screen](JOINT-MASK04-EXTERNAL-RAM-ECHO-SCREEN.md),
the same route increases the late `3FA` difference, so C4 remains open.
The next useful C4 or C3 candidate needs a consumer or alternate return
that retains a decision or selectively reduces echo under independent
controls; G2 stays active.

Run `python3 g2/joint_mask04_ram_return_arithmetic.py` from the
microcode directory. The [machine report](results/joint-mask04-ram-return-arithmetic.json)
records full-trace digests, source hashes, row counts and the distinct
input, register, carry and output values for every window.
