# The `3FC→3FD` path recodes a delayed RAM nibble through the real ROM

The [word-level audit](joint_mask04_ram_carry_3fc_arithmetic.py) replays the
own-echo, independent remote, mixed and zero inputs from the
[`3FD` challenge](JOINT-MASK04-RAM-CARRY-3FD-ECHO-SCREEN.md). It checks
every reached `3FC` and `3FD` in the 128-sample training window: **6,000
visits at each word for each input**, or 48,000 checked word equations.
All four full runs sustain 9,000 ADC visits and execute 288,047 real-PROM
words. The audit reconstructs pre-word internal RAM from every register
write, checks the two-slice instruction pair, ALU F/Y, selected D and
register destination, and checks that each `3FD` ROM address is
`0x100 +` the immediately preceding `3FC` Y.

At `3FC`, the executed low/high instructions are `45/C5`, with A=R10,
B=R13. Their checked result is an eight-bit addition of returned RAM D,
pre-word R10 and the low-slice carry input, with only R13's high nibble
written. At **all 24,000 training visits**, R10=`10` and carry-in=0,
so `Y3FC=(D+0x10)&0xff`. The return drives
D's low nibble to `1`, and the reached values are `01`, `11`, `21`,
`31` and `91`.

At `3FD`, the executed pair is `94/C5`, with A=R5, B=R10. The low
slice computes `~R5lo + carry`; the high slice adds ROM D high nibble,
R5 high nibble and low carry. The low Y output selects R5's low nibble,
while the computed F is written to R10. At **all 24,000 training visits**,
R5=`00` and carry-in=1, giving a low-slice carry-out of one and
`Y3FD=(((ROM>>4)+1)&15)<<4`. The checked real-ROM chain is:

| RAM D at `3FC` | `3FC` Y | `3FD` ROM address | ROM byte | `3FD` Y |
| --- | --- | --- | --- | --- |
| `01` | `11` | `111` | `33` | `40` |
| `11` | `21` | `121` | `5C` | `60` |
| `21` | `31` | `131` | `76` | `80` |
| `31` | `41` | `141` | `1E` | `20` |
| `91` | `A1` | `1A1` | `12` | `20` |

This is a genuine executed delayed-input-to-ROM transform under the
assumed RAM mux. It explains why the `3FD` byte changes with own and
remote training, and why `31`/`91` stored codes collide at the proposed
Y output. Neither operand at these two calculations contains a varying
trained coefficient in the tested fixture. R10 changes elsewhere in the
loop, but it returns to `10` before every checked `3FC`; R5 is `00`
before every checked `3FD`. The prior full-trace comparison also finds
Q, TEST and control path unchanged. A different mode, mux timing or
output circuit could behave differently; the RAM/TEST/latch wiring is
not verified. C4 remains open, and the codebook is not an analog line
residual. Next seek a photo-compatible mode/return that changes a
consumed operand or an independently constrained line-output path.

The [machine report](results/joint-mask04-ram-carry-3fc-arithmetic.json)
contains all trace/input hashes, equation counts, and early/late operand,
ROM and output distributions. Reproduce from this directory with
`python3 g2/joint_mask04_ram_carry_3fc_arithmetic.py`.
