# Input-derived dispatch candidate at 109

Under the fitted-original mapping and the tested reset path, the first visit
to 109 has R0=255−D, Q=0, and carry input 1. The decoded operation is
`~R0 + Q + 1`, so current ALU Y is `(D+1) mod 256`. The preceding instruction's
Y and Q are both zero. These values make the index-source alternatives
experimentally distinct.

The existing eight-entry table hypothesis sends 109 to one of the branch
instructions 10A–111. If the index comes from current Y, the first selected
entry is `(D+1) AND 7`:

| Entry | Input D modulo 8 | Branch word | Encoded destination |
| --- | ---: | --- | --- |
| 0 | 7 | 10A | 11A |
| 1 | 0 | 10B | 148 |
| 2 | 1 | 10C | 18B |
| 3 | 2 | 10D | 300 |
| 4 | 3 | 10E | 259 |
| 5 | 4 | 10F | 345 |
| 6 | 5 | 110 | 09E |
| 7 | 6 | 111 | 133 |

This supplies a concrete input-code-dispatch interpretation for this local
path, without using a randomly chosen index. It is an alternative scenario,
not recovered hardware wiring or a change to the default. Q or preceding-Y
indexing instead chooses entry zero for every constant input byte in these
reset fixtures. The historical scenario index 2 chooses entry two.

## Controlled comparison

[dispatch109_study.py](dispatch109_study.py) compares the four source choices
at **only** 109. All other computed transfers retain the baseline's scenario
index 2. Initial RAM/Q are zero, external D is held constant, and the existing
original-role, previous-flag, defined logical-carry assumptions are retained.
The [configuration](dispatch109-study.json) declares every varied source and
the initial preceding-Y value.

For every source, all 256 input bytes run for 1,000 cycles. The checker confirms
the register preconditions, current and previous Y, Q, selected input index,
and first branch target directly from the integrated trace. It records visited
instructions and repeated modeled states rather than interpreting clean runs
or higher coverage as proof of useful modem processing.

The repetition key includes next PC, all register RAM, Q, ALU flags/Y, and the
complete stack state. With constant D and constant scenario indices elsewhere,
these values determine future modeled execution; no random dispatch remains.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/dispatch109_study.py
```

The [report](results/dispatch109-study/report.json) contains per-source coverage,
first-entry and repeat-period counts, every run's first-dispatch state and trace
digest, and source hashes. Twenty-four witnesses retain complete traces and
mapping/scenario files.

## Measured outcomes

All 1,024 runs complete without model or stack errors. Aggregate visited
instructions across each source's 256 runs are:

| Index source | First table entries | Distinct instructions visited |
| --- | --- | ---: |
| Scenario index 2 | Only 2 | 168 |
| Current Y | All eight, 32 inputs each | 476 |
| Q | Only 0 | 107 |
| Preceding Y | Only 0 | 107 |

In the current-Y profile, 130 inputs reach the terminal self-loop at 084.
The remaining cases repeat near 1EC/1ED (32), 36C (32), 127–12A (31),
298–29D (30), or 187/188 (one). Every run has an observed repeated modeled
state within the recorded 1,000 cycles. This is varied control-flow execution,
not a sustained signal-processing workload. These counts are not combined
with the different assumptions used for the earlier 941-word sequencer sweep.

## Limits and next discriminator

This is stronger than a freely selected branch because one computed value
predicts the branch for every tested input byte. It remains conditional on both
the datapath decode and the assumed table base/stride/index truncation. It does
not establish which device supplies D, whether D is stable in real operation,
or that later visits to 109 share the reset preconditions.

Current-Y indexing must not be selected merely because it exercises more of
the program. Further evidence should test whether callers and downstream
routines use the resulting input classes coherently, and whether a compatible
physical address path could supply this table index. The fixed-index and
seeded-dispatch studies remain separate, reproducible hypotheses.
