# Changed line level exposes three more executed receive phase states

The [frozen four-state holdout](JOINT-MASK04-Q05-PHASE-STATE-HOLDOUT.md)
recovered two nonzero payloads at nominal level. This
[challenge](joint_mask04_q05_phase_level.py) reuses the second payload
in each selector but fixes analog gain from the separate zero-run
calibration, then applies 0.75, 1.0 or 1.25 level before ADC
quantization. It keeps the ROM-sensitive `12A` transmitter, six-sample
line alignment, Q=0.5 filter, real-PROM mask-04 receiver and frozen
46/93 phase rule. The external known-carrier decoder is 0/64 wrong
in every level/mode fixture.

| Selector | Level | Executed four-bit states | Data wrong / unknown | Preamble/pipeline unknown |
| --- | ---: | --- | ---: | ---: |
| `40` | 0.75 | `5,9,B,C,D` | 0 / 17 | 0 |
| `40` | 1.00 | `5,8,C,D` | 0 / 0 | 0 |
| `40` | 1.25 | `6,8,C,D` | 0 / 14 | 32 |
| `60` | 0.75 | `5,9,B,C,D` | 0 / 17 | 0 |
| `60` | 1.00 | `5,8,C,D` | 0 / 0 | 0 |
| `60` | 1.25 | `6,8,C,D` | 0 / 18 | 32 |

The nominal four-state rule only knows `5,8,C,D`. The 75% cases
introduce `9,B`; the 125% cases introduce `6`. There are no known
wrong decisions, but incomplete line bytes prevent modeled USART
handoff at the changed levels. The machine report saves every
per-symbol state, expected dibit and pair of executed `3F8` Y bytes
for a phase-consistency audit.

The [subsequent audit](JOINT-MASK04-Q05-PHASE-LEVEL-MAP.md) finds one
consistent phase extension for these states and tests it on the
answer selector. The result concerns an external receive consumer;
ADC timing, latch, analog gain and USART wiring are still assumed.

The [machine report](results/joint-mask04-q05-phase-level.json) records
six transmitter/receiver trace and PCM/ADC hashes plus all decisions.
Reproduce with `python3 g2/joint_mask04_q05_phase_level.py` from the
microcode directory.
