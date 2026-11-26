# Phase-47 receiver state changes with signal level but supplies no tested adaptive decision

The [joined gain/bias challenge](JOINT-MASK04-FULL-ZERO-ANALOG-VARIANTS.md)
made the frozen receive table abstain despite an independently decodable
transmitted signal. This [state probe](joint_mask04_rx_state_level_probe.py)
replays the call selector's nominal PCM and its 0.75-gain, +16-count
variant. Their reconstructed transmitter samples hash-match the saved
real-PROM Y7 run. Each receiver executes **768,047 real-PROM words**;
the new trace digest and ADC-stream hash exactly match the previously
saved nominal and altered receive runs.

At ADC visit 47 of each of 64 A3/A4 symbols, the probe records the
executed `3ED` row-0 and row-3 Y bytes, Q and all 16 modeled Am2901 RAM
bytes after row 3. Comparing the two input levels:

| State at phase 47 | Symbols changed out of 64 | Distinct nominal / altered values |
| --- | ---: | ---: |
| R0 | 24 | 4 / 2 |
| R1 | 24 | 5 / 3 |
| R12 | 24 | 4 / 3 |
| Q | 24 | 4 / 2 |
| Each of the other 13 RAM bytes | 0 | 1 / 1 |

R1 equals the captured row-3 Y byte in all 64 symbols at both levels;
it is not an independent gain estimate at this capture site. R0, R12
and Q react to the changed ADC stream, but these two runs do not show
that any one of them encodes gain, midpoint or a usable decision
threshold. A slowly varying value could be held externally or written
at another visit or mode, so the constant bytes do not exclude gain
control elsewhere.

The previously frozen [phase-47 Boolean readout](RECEIVER-MASK04-PHASE47-BOOLEAN-DIBITS.md)
is also tested without modification on these executed-Tx captures. It
makes **11/63** dibit errors at nominal level and **11/63** at the
changed level, with different error positions. That rule had worked on
some reference-generated PCM but was already known to be sensitive to
carrier phase; this result confirms it cannot simply replace the
46/93 table on the joined waveform. Neither rule is identified as the
Nokia receiver's output circuit. C3 remains open.

Next inspect state at other receive visits or a photo-compatible
external latch/AGC path, then freeze a decision rule before testing
fresh executed-transmitter streams and the controller handoff. The
[machine report](results/joint-mask04-rx-state-level-probe.json) stores
all per-symbol RAM/Q and row captures. Reproduce from the microcode
directory with `python3 g2/joint_mask04_rx_state_level_probe.py`.
