# A sample-paced `3FA` Y latch cannot rescue the tested echo proxy by phase

The [latch-phase replay](joint_mask04_ram_carry_latch_phase.py) tests the
remaining simple consumer of the [transient `3FA` feedback output](JOINT-MASK04-RAM-CARRY-PROPAGATION.md):
capture one `3FA` Y byte per held ADC sample. It re-executes the same
four real-PROM inputs—zero, own transmit echo, independent remote signal,
and their mixture—with both write-only and three-sample high-nibble RAM
readback. TEST uses previous carry. Each of the eight runs executes
288,047 words and completes 9,000 ADC visits without leaving the four-row
loop. The hypothetical latch edge is swept over all 46 visit offsets
available in every 47/46-visit ADC sample.

All eight runs have **zero samples with a changing `3FA` Y byte inside the
held sample**. Consequently every one of the 46 latch phases captures the
same byte for each sample. At every phase the late 32-sample code-space
comparisons are:

| Route | Mixed versus remote | Own echo versus zero | Remote versus zero |
| --- | ---: | ---: | ---: |
| Write-only control | 0.4375 | 0 | 0.3125 |
| High-nibble return | 17.8125 | 6.0 | 8.8125 |

The numbers are mean absolute **unsigned Y-byte differences**, not analog
line residuals. None of the candidate latch phases reduces mixed-versus-remote
contrast relative to the same-phase write-only control while retaining remote
response. The late own-echo-versus-zero contrast also rises from zero to six.
Thus choosing a different fixed latch phase within the ADC hold cannot
explain away the earlier growing `3FA` contrast under this route.

This narrows only the proposed sample-paced `3FA` Y capture. The Y-to-latch
and latch-to-line wires, RAM, TEST source, ADC range and sample clock remain
assumed; a different output mapping, mode-qualified return or analog circuit
could behave differently. C4 still needs an identified line residual that
falls selectively during training and stays frozen when commanded. The next
test should put trained state into a later consumed operand or use a
photo-compatible output circuit with an explicit analog transfer function;
G2 remains active.

The [machine report](results/joint-mask04-ram-carry-latch-phase.json) records
all 46 phase comparisons, input and trace hashes, and the within-sample
constancy check. Reproduce from this directory with
`python3 g2/joint_mask04_ram_carry_latch_phase.py`.
