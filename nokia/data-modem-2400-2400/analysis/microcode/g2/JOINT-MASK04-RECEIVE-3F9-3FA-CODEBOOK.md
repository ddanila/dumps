# The executed `3F9` and `3FA` Y bytes recode the current ADC nibble

The [replay](joint_mask04_receive_3f9_3fa_codebook.py) executes the real
mask04 PROM path for one legal eight-dibit reference waveform at carrier
starts of 0°, 45° and 90°. Each case supplies 64 complementary ADC samples
held for 47/46 visits and runs 96,047 microinstructions. The independent
reference receiver recovers the intended dibits in each case. The 0°
trace digest exactly matches the earlier varying-waveform baseline.

The cycle trace corrects a possible timing misunderstanding: `3F8`, `3F9`
and `3FA` each execute **once per ADC visit**; `3ED` executes four times.
The new capture records the sole Y byte at each `3F9` and `3FA` visit.
Across 9,000 ADC visits and all sixteen current ADC high nibbles:

| Executed Y site | Distinct values | Current-nibble conflicts | Adjacent pairs checked | Pair conflicts |
| --- | ---: | ---: | ---: | ---: |
| `3F9` | 15 | 0 | 110 | 0 |
| `3FA` | 2 (`20`, `21`) | 0 | 110 | 0 |

`3F9` is almost a one-to-one recoding of the current high nibble; only
inputs `9` and `D` collide at output `31` in this codebook. `3FA` yields
`21` for current nibbles `6`, `B` and `C`, and `20` for the other thirteen.
No output at either site depends on which previous ADC nibble occurred
among the 110 observed adjacent pairs. The previously tested one-sample
`1F`/`6F` pulse does distinguish both sites, but that distinction is still
consistent with processing the **current quantized sample**, not a recovered
dibit or accumulated carrier phase.

This result constrains proposed `3F9`/`3FA` latch routes under the direct
`D3EB=01` fixture. A decoder of their Y bytes alone would be an external
decision built on a recoded ADC stream. The real-ROM lookup and arithmetic
are executed, but a later decision or physical latch remains untraced.
Next test whether the transient Q/RAM or a mode/feedback route emits a
history-dependent bit during actual symbol transitions, then follow any
candidate bit to controller/USART RxD. Continue with explicit
photo-compatible assumptions; C3 remains open.

The [machine report](results/joint-mask04-receive-3f9-3fa-codebook.json)
contains the full 16-entry Y codebooks and trace/input hashes. Reproduce
from this directory with
`python3 g2/joint_mask04_receive_3f9_3fa_codebook.py`.
