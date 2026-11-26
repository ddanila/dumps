# Where the sustained high-RAM return stops propagating

The [paired full-word trace](joint_mask04_ram_carry_propagation.py) compares
the same-input write-only control with the `3F9`-latched high-nibble RAM
return used in the [own/remote/mixed challenge](JOINT-MASK04-RAM-CARRY-ECHO-SCREEN.md).
The declared route writes a sample-paced, 256-by-8 external memory and reads
its value three samples later as the high nibble of D at `3FA`, with D's low
nibble fixed to `1`. TEST uses previous carry, polarity 1. Writes stop after
sample 25 in the 64-sample varying waveform and after 128 samples in the
192-sample remote-plus-own-echo waveform. Both sides have identical ADC input,
initial internal RAM, RAM address timing and write gate; only the readback
switch changes.

| Input | PROM words per run | ADC visits | Changed `3FA` ALU / writes | R13 difference spans |
| --- | ---: | ---: | ---: | ---: |
| Varying, 64 samples | 96,047 | 3,000 | 1,219 / 1,219 | 1,219 |
| Remote + own echo, 192 samples | 288,047 | 9,000 | 6,000 / 6,000 | 6,000 |

Both paired runs sustain the complete four-row loop and have identical PC
paths. The external-read record changes at every `3FA` visit because the
selected source differs; that count does not mean every D value differs.
Every actual ALU or register-write difference is at `3FA`. Q, TEST, and all
other ALU words and register writes agree. Reconstructing all 16 internal
RAM bytes after every word finds **only R13 different**: each difference
lasts exactly six cycles, from `3FA` through `3FB`, and rejoins when `3FC`
overwrites R13. This holds for all 1,219 and 6,000 spans, respectively.
Final internal RAM and Q are equal in each pair.

For example, the first changed `3FA` is cycle 4,577. The changed R13
survives `3ED`, `3EA`, `3EB`, `3EC` and `3FB`; `3FC` writes the same R13
in both runs. Thus this candidate feedback changes a transient `3FA`
code and its short-lived R13 destination, but does not modify a later
executed arithmetic word, condition, or program branch on either tested
stream. The tested `3FA` code contrast is therefore not evidence that
the microprogram has retained and consumed an echo estimate.

This excludes propagation through the **tested** previous-carry,
high-nibble, three-sample return under these two legal inputs. It does
not rule out an external latch capturing `3FA` Y, another mode or return
timing, or a different consumed output. The RAM, TEST mux and output-latch
wiring remain photo-compatible assumptions; no analog line residual or
received bit is identified. For C4, seek a photo-compatible latch at
`3FA` with a measurable line consequence, or a feedback route whose
stored state survives into a later consumed operand. Keep G2 active and
C4 open.

The [machine report](results/joint-mask04-ram-carry-propagation.json)
contains paired trace digests, PC digest, per-word difference counts,
all R13 span lengths and rejoin PCs. Reproduce from this directory with
`python3 g2/joint_mask04_ram_carry_propagation.py`.
