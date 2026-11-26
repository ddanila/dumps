# A new carrier start exposes a failure in the frozen receiver gates

The [phase-112 replay](joint_mask04_12a_row0_boolean_phase112.py) uses the
unchanged 20-state row-phase gates, one fresh eight-byte payload per selector,
the same Q=0.5/+6 analog candidate and fixed gain, and R1 offset 112. It
executes the real q3/mask-04 transmitter and receiver PROMs and captures the
same `3F8` and row-0 `3ED` observations as the prior offset-88 holdout.

| Selector | Source bytes | Independent reference errors / 64 | Frozen-gate errors / 64 |
| --- | --- | ---: | ---: |
| Call `40` | `3A C7 95 E0 6D 12 B4 5F` | 2 | **12** |
| Answer `60` | `D6 09 7B A4 21 FE 58 C3` | 1 | **9** |

The frozen gates do not recover the offered line bytes or the source payload
at this offset. The independent reference errors mean this is also a boundary
of the assumed line/phase fixture, not an isolated test of the gate. The gate
errors occur at different symbols from the reference errors, so that fixture
failure does not by itself explain them.

The [transition-graph audit](joint_mask04_12a_row0_phase112_audit.py) joins
the untouched 20-state development graph to these two holdout streams for
*diagnosis only*. The combined 22-state graph has one connected component,
zero contradictions and leaves every old phase label unchanged. New state
`12` needs phase 3, which the gates already predict. New state `5E` needs
phase 0, but the frozen gates output phase 1. Every one of the 12 call and
9 answer gate errors touches `5E`; assigning it phase 0 after seeing the
answers would remove those errors. That assignment is **not** a validated
repair or evidence for a Nokia phase-logic circuit.

This narrows the next C3 experiment. Treat phase-112 labels as development
data if the gates are revised; freeze any new rule before an untouched
payload/phase-start test. Separately test a line candidate whose independent
reference is exact at the challenged phase, then check whether the same
`5E` mismatch persists. Keep the ADC, row capture, phase gates and
USART-01 route as labelled assumptions; C3/G2 remain active.

The [executed report](results/joint-mask04-12a-row0-boolean-phase112.json)
contains PROM trace digests, PCM/ADC hashes, row observations, gate states,
readout and source hashes. The [audit report](results/joint-mask04-12a-row0-phase112-audit.json)
records the new-state constraints. Reproduce from the microcode directory:

```sh
python3 g2/joint_mask04_12a_row0_boolean_phase112.py
python3 g2/joint_mask04_12a_row0_phase112_audit.py
```
