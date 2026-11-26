# A `3FC` RAM return reaches the next ROM calculation, then rejoins

The [paired full-word replay](joint_mask04_ram_carry_3fc_propagation.py)
tests a different photo-compatible return from the four photographed
external RAMs. The prior `3FA` return changes only its own output and a
short-lived R13 write. The executed trace shows `3FB` reading the Am27S31
ROM, while `3FC` takes a scenario D byte, so this replay returns the same
three-sample-delayed high RAM nibble at `3FC`. It keeps the `3F9` Y latch,
sample-paced 256-by-8 RAM, previous-carry TEST assumption, write gate,
ADC input and initial state identical to the write-only control.

| Legal input | Words per run | ADC visits | Changed ALU sites | Changed ROM reads at `3FD` |
| --- | ---: | ---: | --- | ---: |
| Varying 64 samples | 96,047 | 3,000 | `3FC`: 1,219; `3FD`: 1,219 | 1,219 |
| Remote + own echo, 192 samples | 288,047 | 9,000 | `3FC`: 6,000; `3FD`: 6,000 | 6,000 |

Both pairs sustain the complete four-row receive loop with identical PC
paths. In the first varying-stream difference, returning `21` rather than
the stub `01` at `3FC` changes Y from `11` to `31`. The following `3FD`
ROM read changes from address `111`, byte `33`, to address `131`, byte
`76`; its Y and R10 write change from `40` to `80`. Thus the delayed RAM
byte enters a **second executed arithmetic/ROM operation**. This is a
substantive contrast with the `3FA` return, which did not change any later
ALU word.

The effect is still local. Across the full runs, Q and TEST records never
differ, and neither program path changes. Only R10 and R13 ever differ in
reconstructed internal RAM; R13 rejoins at `3F2` after each ten-cycle
difference span, and both final RAM states agree. No later ALU site beyond
`3FD` differs, and the tested `3ED` output remains unchanged. The changed
`3FD` byte is an output candidate, not an identified echo residual.

The RAM-to-D selection at `3FC`, TEST mux and any Y latch remain assumed.
The next C4 test should compare `3FD` Y under own echo, remote, mixed and
zero inputs against a same-input write-only control, including training
and frozen windows. A selective falling line residual is still required
to establish echo cancellation; C4 remains open and G2 active.

The [machine report](results/joint-mask04-ram-carry-3fc-propagation.json)
contains paired trace and PC digests, per-site differences, all-register
state comparison and R13 span/rejoin counts. Reproduce from this directory
with `python3 g2/joint_mask04_ram_carry_3fc_propagation.py`.
