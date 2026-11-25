# Two executed receive-row bytes carry a generalizing phase code

The [single-byte latch test](RECEIVER-MASK04-3ED-PROM-LATCH.md) and
[single-nibble phase test](RECEIVER-MASK04-LATCHED-NIBBLE-PHASE.md) did not
recover reference dibits. Their full-PROM traces captured four `3ED` Y bytes
per ADC visit. Rows 1 and 2 are always zero in the eleven streams tested
here; rows 0 and 3 vary. This [row-pair screen](receiver_mask04_rowpair_phase_code.py)
tests `(row0 Y, row3 Y)` as one phase-code state at a fixed visit within
each symbol. It reruns all eleven 192,047-instruction real-PROM receive
fixtures and checks every capture hash against the earlier latch report.

The diagnostic assigns a phase quadrant to each observed pair. It asks
whether the quadrant difference between adjacent symbols equals the
reference dibit's phase step plus a fixed carrier advance. The reference
1,800 Hz carrier rotates 1.5 cycles per 1,200-baud symbol, so the expected
carrier term is **two quadrants** (180°). The search covers all 375 ADC visits
per symbol, lags −2…+2, both phase orientations and all four carrier terms.
It fits the codebook using only 36 dibits from two periodic and one random
stream, then freezes the choice before testing independent streams.

| Data source and fixed readout | Training | Holdout | Fresh random | Coverage on independent dibits |
| --- | ---: | ---: | ---: | ---: |
| Executed `3ED` row-0/row-3 pair, selected eight-state codebook | 0/36 errors | **0/48** | **0/48** | **96/96** |
| Best training-exact raw-ADC one- or two-sample codebook | 0 training errors | — | — | At most **11/96** |

Ten row-pair choices fit training exactly. The training-only ranking of
fewest states, earliest phase and positive orientation selects ADC-visit
phase 0, lag 0 and carrier term 2. Its eight states form one connected
phase-label graph, and every holdout/fresh transition uses known states.
Phase 47 also generalizes with the same eight-state count. The eight
phase-quadrant assignments selected at phase 0 are:

| Row 0 Y | Row 3 Y | Relative phase quadrant |
| ---: | ---: | ---: |
| `00` | `F2` | 1 |
| `F1` | `F2` | 1 |
| `F2` | `F8` | 2 |
| `F3` | `F5` | 3 |
| `F4` | `F8` | 0 |
| `F5` | `F5` | 3 |
| `F5` | `F8` | 2 |
| `FD` | `F8` | 0 |

The raw-ADC control uses the **same** three training and eight independent
streams, phase-step constraints, lags, orientations and carrier terms. It
tries each of eight within-symbol single ADC samples and seven adjacent
two-sample pairs. Many raw choices fit training because they memorize
22–29 fine-grained sample states, but their frozen codebooks barely cover
new streams. The compact executed row-pair code is therefore stronger
evidence of a reusable phase representation than a training fit alone.
It is still a **conditional** result under the mask-`04` field map,
complementary ADC input, four-row dispatch and proposed PROM/NAND capture.

The quadrant lookup and differential subtraction in this experiment are
external diagnostics; no executed DSC instruction or photographed logic
has yet been shown to turn these two bytes into USART-01 RxD. Nor has the
ADC path or U19/U12 latch wiring been continuity-verified. C3 remains open.
The [changed-input-level replay](RECEIVER-MASK04-ROWPAIR-LEVEL-CHECK.md)
shows that this frozen eight-state lookup does not generalize to a 0.75-gain
waveform that the independent receiver still decodes. It is a phase-state
lead at one input level, not a complete decision rule.
The next test is to identify an executed or photo-compatible consumer of
the row-0/row-3 state and test its bit at USART timing, including a changed
input-level fixture. The [machine report](results/receiver-mask04-rowpair-phase-code.json)
contains all choices, validation scores, trace/capture hashes and source
hashes. Reproduce from the microcode directory with
`python3 g2/receiver_mask04_rowpair_phase_code.py`.
