# Where the frozen receive circuit fails as gain changes

The [phase-131 matched test](JOINT-MASK04-12A-MODE-PHASE131-GAIN.md)
showed that the frozen package-budgeted phase circuit fails at 1.25×
receive gain. This sweep keeps its real-PROM transmitter bytes, carrier
start, two controller payloads, Q=0.5 line and assumed `81→A1` mode
schedule fixed. The [ADC-range reconstruction](joint_mask04_12a_mode_phase131_adc_range.py)
reproduces the exact baseline and 1.25× PCM hashes and saves the selected
line waveform. The [1.125× run](joint_mask04_12a_mode_phase131_intermediate_gain.py)
and [boundary runs](joint_mask04_12a_mode_phase131_gain_boundary.py)
then execute the real receiver PROMs at intermediate gains.

| Gain | Modeled clipped PCM samples, call/answer | New capture states | Frozen package errors, call/answer |
| ---: | ---: | --- | ---: |
| 1.000× | 0 / 0 | `4C` | 0/64, 0/64 |
| 1.125× | 0 / 0 | `02`, `6E` | 0/64, 0/64 |
| 1.150× | **0 / 0** | `48`, `5D` | **12/64, 11/64** |
| 1.175× | 3 / 2 | `48`, `5D`, call-only `42` | 12/64, 11/64 |
| 1.250× | 6 / 3 | `2F`, `42`, `48`, `5D` | 16/64, 10/64 |

The new-state column is relative to previously observed labels at
lower gains; each row also contains some already seen states. The first
tested failure is between **1.125× and 1.150×**, before any modeled
PCM sample clips. Clipping cannot by itself explain the failure. At
1.150× the old 12-state cover misses 21/64 call and 18/64 answer
decisions, while the frozen package circuit misses fewer but still
delivers the wrong dibits. Reference decoder errors remain two call
and zero answer at each tested gain.

The [joined graph audit](joint_mask04_12a_mode_phase131_gain_graph_audit.py)
propagates phase constraints through states shared across successive
real-PROM runs. It finds **zero conflicts** and derives seven additional
mode-`81/A1` labels: `02→3`, `2F→0`, `42→3`, `48→2`, `4C→1`, `5D→1`,
`6E→0`. The frozen circuit differs only at `48` (predicts 3, needs 2)
and `2F` (predicts 1, needs 0). Every wrong decision at 1.150×,
1.175× and 1.250× crosses into or out of those states. Phase bit 1
remains correct on all 42 combined mode-conditioned labels; phase bit 0
is the failing output. A single photographed U15 still cannot directly
encode phase bit 0 from the seven captured bits plus the assumed mode
wire on these labels, in either output polarity. A different multistage
path or capture feature is needed for this fixture.

The [ADC range](results/joint-mask04-12a-mode-phase131-adc-range.json),
[1.125× run](results/joint-mask04-12a-mode-phase131-intermediate-gain.json),
[boundary runs](results/joint-mask04-12a-mode-phase131-gain-boundary.json)
and [graph audit](results/joint-mask04-12a-mode-phase131-gain-graph-audit.json)
preserve the waveform, hashes, capture states, transition errors and
source files. Reproduce from the microcode directory with:

```sh
python3 g2/joint_mask04_12a_mode_phase131_adc_range.py
python3 g2/joint_mask04_12a_mode_phase131_intermediate_gain.py
python3 g2/joint_mask04_12a_mode_phase131_gain_boundary.py
python3 g2/joint_mask04_12a_mode_phase131_gain_graph_audit.py
```

These are executions under a candidate DAC/line/ADC and external gate
route. The gain, physical capture bits, mode net and USART wires are
still assumptions. C3 and G2 remain open. Next test a changed capture
bit or edge at the same saved line input against the now localized
`48`/`2F` failures; a surviving logic route needs a fresh holdout before
being treated as more than a fitted hypothesis.
