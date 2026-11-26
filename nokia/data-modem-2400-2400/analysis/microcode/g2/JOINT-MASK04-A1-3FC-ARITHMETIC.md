# `A1` shifts the `3FC` ROM lookup without a trained operand

The [held-`A1` echo challenge](JOINT-MASK04-A1-RAM-3FC-ECHO.md) changed
`3FD` output codes but did not attenuate echo. This
[full-trace audit](joint_mask04_a1_3fc_arithmetic.py) replays the same
four return-route inputs, checks their ADC and trace hashes against the
echo challenge, and verifies the split-slice instruction, D operand,
ALU F/Y, register write and ROM address at every training visit.
All four runs sustain 288,047 real-PROM words. There are **24,000
checked `3FC` equations and 24,000 checked `3FD` equations**.

The consumed operands are constant throughout the training window:

| Pre-word operand | Mode `01` | Held `A1` |
| --- | ---: | ---: |
| `3FC` R10 | `10` | `20` |
| `3FC` carry-in | 0 | 0 |
| `3FD` R5 | `00` | `00` |
| `3FD` carry-in | 1 | 1 |

At `3FC`, the executed `45/C5` pair computes
`Y3FC = (RAM_D + 0x20) & 0xFF` in this `A1` fixture, then uses that
byte to address the Am27S31 at `0x100 + Y3FC` for `3FD`. The
executed `94/C5` pair writes its computed F to R10 and emits Y from
the ROM high nibble plus the fixed R5/carry combination. The reached
codebook includes:

| RAM D | `3FC` Y | ROM address / byte | `3FD` Y |
| --- | --- | --- | --- |
| `01` | `21` | `121` / `5C` | `60` |
| `21` | `41` | `141` / `1E` | `20` |
| `31` | `51` | `151` / `15` | `20` |
| `41` | `61` | `161` / `0F` | `10` |
| `A1` | `C1` | `1C1` / `FD` | `00` |

Every mode-`01` comparison has pre-`3FC` R10=`10` for the same 6,000
visits per input. Held `A1` changes that constant to `20`; it does
not introduce a time-varying coefficient at these two consumed
operands. The changed `3FD` contrast is therefore an altered fixed
lookup of delayed input codes under this route, consistent with the
observed lack of training attenuation. The frame-to-`3EB`, RAM mux,
TEST and output latch are still assumed, and a codebook is not an
analog residual. C4/G2 remain open; test a mode transition or another
photo-compatible return that reaches a varying consumed operand.

The [machine report](results/joint-mask04-a1-3fc-arithmetic.json)
contains all per-input equations, codebooks, windows and source hashes.
Reproduce with `python3 g2/joint_mask04_a1_3fc_arithmetic.py` from
the microcode directory.
