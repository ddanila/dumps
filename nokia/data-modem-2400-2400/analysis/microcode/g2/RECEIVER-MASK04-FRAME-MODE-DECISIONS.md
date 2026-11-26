# Controller frame bytes leave the tested two-visit receive features intact

The [earlier mode-edge test](RECEIVER-MASK04-FRAME-MODE-3EB.md) found that
offering the controller's observed third-frame bytes `81` and `A1` at
the mask-`04` receiver's wrapper input `3EB` changes arithmetic but
does not leave a train/freeze history after a completed row. That
result did not test the later frozen two-visit receive readout. This
[replay](receiver_mask04_frame_mode_decisions.py) checks whether the same
photo-compatible, **untraced** controller-to-`3EB` route would disrupt
the candidate demodulator.

For each of 75° and 165° carrier rotation, the script executes four
192,047-instruction real-PROM runs with the same 16-symbol stream:
eight `11` preamble symbols and eight seed-`B417` data symbols. The
fixtures hold `01`, hold `81`, hold `A1`, or switch `81→A1` halfway
through the 24,001 wrapper visits, exactly at the symbol-8 boundary.
Every run selects 6,000 complementary ADC bytes at `3F8`, receives all
24,001 wrapper bytes, and has 6,001 candidate raw-PROM latch edges.

| Carrier angle | `01` | `81` | `A1` | `81→A1` |
| ---: | ---: | ---: | ---: | ---: |
| 75° | 0 wrong, 0 unknown / 15 | 0 / 0 | 0 / 0 | 0 / 0 |
| 165° | 0 wrong, 0 unknown / 15 | 0 / 0 | 0 / 0 | 0 / 0 |

The full PROM trace digest changes for every mode fixture, so the mode
input is active. Yet all 32 selected `3F8` Y5–Y7 capture values at visits
47 and 94 are identical within each angle, and the frozen primary/alternative
consensus emits the same 15 dibits. This narrow invariance means that
the direct `3EB` frame-byte hypothesis does not invalidate this
candidate receive readout on the tested stream. It does not establish
that the controller byte is physically connected to `3EB`, nor does it
show echo cancellation. The earlier edge run's lack of retained mode
history still prevents calling `81→A1` a train/freeze control.

Next challenge the same route with longer independent streams and an
identified RxD/RxC/SYNDET consumer, or try another mode-input lane for
C4. The [machine report](results/receiver-mask04-frame-mode-decisions.json)
contains every capture, decision, trace digest and source hash. Reproduce
from the microcode directory with
`python3 g2/receiver_mask04_frame_mode_decisions.py`.
