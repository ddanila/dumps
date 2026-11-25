# A divided PROM edge reproduces the joined DAC sample stream

The [raw-edge phase check](PHOTO-TX-PROM-LATCH-PHASE.md) found that U10 D2
rises at `129` and falls at `12A` in the recurring transmit loop. This
replay applies a concrete **clock hypothesis** to the uninterrupted
controller-driven A1 tone → A2 capture-off → A3 reversals → A4 data
execution. It counts actual U10 D2 edges in each real-PROM trace, clocks
once per 375 edges, and captures the ALU Y byte that was available at the
preceding instruction. The divider, edge wiring and 74LS273 data path are
assumed, not identified board nets.

Both 8031 controller selector modes complete **1,248,256** microinstructions
cleanly. Each has **312,054** U10 D2 rises at `129` and the
same number of falls at `12A`. A counter reset at the first `127` and
divided by 375 yields **832 samples**, spaced exactly 1,500
microinstructions apart. With one instruction per 14.4 MHz oscillator
period, that would be 9,600 samples/s. The direct rising-edge hypothesis
captures preceding `128` Y; an inverted falling-edge hypothesis captures
preceding `129` Y. Their byte hashes match the corresponding sites in the
earlier independently executed [full-PROM site replay](PHOTO-JOINT-FREE-CLOCK-SITES.md)
for both controller modes.

For the six DAC bus orders surviving nonperiodic data validation, the same
candidate A2 mid-code gate and fixed 1,950 Hz, Q=1 bandpass give:

| Captured byte | Late A1 2,100 Hz fit R² | A3/A4 pulse-shape fit R² | Matched-filter dibit errors |
| --- | ---: | ---: | ---: |
| Prior `128` Y, direct rise | 0.927–0.928 | 0.794–0.808 | 0/744 |
| Prior `129` Y, inverted fall | 0.721–0.725 | 0.866–0.882 | 0/744 |

Both phases peak at 2,100 Hz and settle to near silence during A2. The
direct-rise phase gives a purer tone under **this fixed filter**, while the
post-ROM phase better matches the independent pulse-shaped data waveform.
The actual analog response, clock polarity and mode-dependent
sampling remain unresolved. The DAC08 bus, A2 gate and line connector are
also still untraced, so C2 remains open.

The [machine report](results/photo-tx-divided-prom-clock.json) records both
full-state trace digests, edge counts, sample hashes and each bus/mode/phase
metric. Reproduce with `python3 g2/photo_tx_divided_prom_clock.py` from
the microcode directory.
