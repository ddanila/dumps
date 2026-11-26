# The `3FC` RAM return makes `3FD` a delayed-input code, not a falling echo residual

The [eight-run challenge](joint_mask04_ram_carry_3fd_echo_screen.py) follows
the [executed `3FC→3FD` dependency](JOINT-MASK04-RAM-CARRY-3FC-PROPAGATION.md).
It feeds four inputs to the same real-PROM receive loop: zero, the modem's
own saved transmit echo, an independent remote waveform, and their mixture.
Each gets a same-input write-only control and a high-nibble return from
sample-paced 256-by-8 RAM, read three ADC samples behind at `3FC`. TEST is
assumed to use previous carry. Training writes stop after 128 samples, and
all streams continue for a common 64-sample zero tail. All eight runs
execute 288,047 words, complete 9,000 ADC visits, and sustain the four-row
loop. Each route performs 24,000 training writes; the return route performs
9,000 RAM reads.

At the proposed `3FD` Y output, the write-only control has **zero code
contrast** among the four inputs. The return route makes `3FD` sensitive
to stored input history, but its late echo contrast grows:

| Window and route | Own echo vs zero | Remote vs zero | Mixed vs remote |
| --- | ---: | ---: | ---: |
| Early 32 samples, write-only | 0 | 0 | 0 |
| Early 32 samples, high return | 29.824 | 31.083 | 40.853 |
| Late 32 training samples, write-only | 0 | 0 | 0 |
| Late 32 training samples, high return | **35.840** | 34.987 | **44.907** |
| Common zero tail, high return | 1.504 | 1.003 | 2.507 |

These are mean absolute **unsigned Y-byte differences** over all visits
in each window, not analog line residuals. Every `3FD` Y byte is constant
within its held ADC sample in all eight runs. A fixed latch phase therefore
cannot change the comparison: over all 46 available phases, early-to-late
own-echo-versus-zero rises from 30 to 36 per sampled code, and
mixed-versus-remote rises from 41 to 45. No phase shows both echo contrasts
falling while retaining a remote response.

After the write gate freezes, each return run differs from its write-only
control for exactly 141 `3FD` visits, the first three 47-visit tail
samples. That matches the declared three-sample read lag: the pointer
then reaches untrained RAM addresses. This is a delayed stored-input
effect, not evidence that learned cancellation weights remain applied
through the common zero tail.

The RAM mux, TEST source, ADC and `3FD` Y-to-line latch are untraced,
photo-compatible assumptions. This result does not rule out another
return, signed output mapping or analog stage. It does exclude selective
training attenuation at this **tested** `3FD` code output under the four
controls. C4 stays open; next audit the `3FC→3FD` arithmetic and lookup
for a trained operand, or test a distinct photo-compatible return with
the same controls. G2 remains active.

The [machine report](results/joint-mask04-ram-carry-3fd-echo-screen.json)
records input/trace/output hashes, RAM activity, whole-visit and 46-phase
comparisons. Reproduce from this directory with
`python3 g2/joint_mask04_ram_carry_3fd_echo_screen.py`.
