# A later receive capture repairs the low-gain phase failure on fresh streams

The [expanded low-gain capture](JOINT-MASK04-12A-LOWGAIN133-EXPANDED-VISITS.md)
found `3F8` Y=`4F` at visit `94` in all six occurrences of unseen state
`1D`. The [mode-1 control replay](joint_mask04_12a_mode1_expanded_controls.py)
adds visit `94` to four previously passing 1.15×/1.25× phase-131 runs.
It exactly preserves their earlier PROM trace and PCM hashes and decision
indices.
The higher-gain failure states give `48→AF` and `2F→2F` at visit `94`.
Thus Y bit 6 is set for the observed `1D` captures and clear for those
two states.

The [candidate gate](joint_mask04_12a_visit94_phase_gate.py) freezes a
new **assumed** later capture and applies
`P0 = frozen_veto_P0 & ~Y6_at_visit94`, leaving phase bit 1 unchanged.
On the six development replays at 0.8×, 1.15× and 1.25× gain, it changes
only the six `1D` symbols, recovers every modeled dibit, and passes the
USART and executed 8031 handoff. The added capture is ready 2,929
microcycles before the first modeled RxC edge. These cases selected the
rule; they are not holdouts.

The [frozen holdout](joint_mask04_12a_visit94_phase_holdout.py) then runs
four new eight-byte controller payloads through the real transmit and
receive PROMs at 0.8× gain, at carrier starts `133` and `135`:

| Carrier start | Selector | Active `1D` symbols | Old veto errors | Later-capture errors | Modeled clipping |
| ---: | --- | ---: | ---: | ---: | ---: |
| 133 | call `40` | 4 | 8/64 | **0/64** | 0 |
| 133 | answer `60` | 2 | 4/64 | **0/64** | 0 |
| 135 | call `40` | 2 | 3/64 | **0/64** | 0 |
| 135 | answer `60` | 4 | 8/64 | **0/64** | 0 |

All four produce the exact offered line bytes and executed controller
source payloads with zero modeled USART errors or overruns. The holdout
activates the new gate on twelve `1D` symbols; it does not test an
additional unseen state. The independent reference receiver has errors
in one of the four cases, so this result is specific to the executed
PROM and assumed external phase circuit.

This is stronger conditional C3 evidence, not a physical C3 pass. The
visit-`94` latch, gate package/fan-out, mode input, ADC/line path, RxD/RxC
and SYNDET connections remain untraced. The phase-bit-0 veto itself also
lacks a package-level realization. Next constrain these captures against
the photographed latch and gate budgets, then challenge a frozen complete
route on another gain/carrier family, including unseen states.

The [control summary](results/joint-mask04-12a-mode1-expanded-controls.json),
[development gate](results/joint-mask04-12a-visit94-phase-gate.json) and
[holdout report](results/joint-mask04-12a-visit94-phase-holdout.json)
retain state/capture values, trace hashes and controller outputs. Reproduce
from the microcode directory with the three linked Python scripts above.
G2 remains active and C3 open.
