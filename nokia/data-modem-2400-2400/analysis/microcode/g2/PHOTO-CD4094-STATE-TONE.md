# A0/A1 frames can select different ROM loops, but not the proposed tone step

The [paired state replay](photo_cd4094_state_tone.py) takes the four-byte
frames actually emitted by the 8031 in states A0 (`80 02 88 7A`) and A1
(`80 02 81 7A`). Under the candidate four-CD4094 cascade, logical chip 1
feeds held D127 and one of chips 0, 2 or 3 feeds held D12C, with either
Q1→D0 or Q8→D0 bit order. The q3 mapping, held-I0 circuit, upper ROM bank,
chip routing and clock are assumptions. A1's 2,605-tick duration suggests a
2,100 Hz handshake interval, but its command meaning is not established.

All 12 real-PROM runs execute 3,000 microinstructions cleanly. Selected
D127/D12C bytes and every PC129/PC12E ROM-address recurrence match the
offered frame. The main state distinction is:

| Candidate chip-1 bus order | A0 D127 | A1 D127 | A0 / A1 second-loop behavior |
| --- | ---: | ---: | --- |
| Q1→D0 | `11` | `81` | Both enter D12C; an odd chip-3 input exits after 255 reads |
| Q8→D0 | `88` | `81` | A0 stays at D127; A1 enters D12C for 613 ROM reads with each even alternate-chip byte |

In the Q8→D0 case, the A1 D12C choices are chip 0=`7A`, chip 2=`02`
and chip 3=`80`. At a hypothesized 9,600 samples/s gate and one or three
oscillator periods per microinstruction, their fixed phase increments per
sample are `B6/92`, `EE/FA` and `80/80`, respectively. None is the ±`38`
step needed for a 2,100 Hz phase walk in this model; the required held bytes
would be `88/78` or `98/68`. Nor do any of the other tested alternate-chip
bytes meet that step condition. No run reaches candidate output `392` or
`39E`. The [machine report](results/photo-cd4094-state-tone.json) records
all 12 input pairs, ROM reads, phase steps, wait cycles and trace digests.

This is a possible controller-state-to-ROM-loop selection under explicit
wiring assumptions. It does not establish that A1 commands the handshake
tone, that these chips drive the DSP, or that the second loop supplies the
DAC08. A decoded D12C step, a different clock, or a separate output consumer
remains necessary for this route to explain the tone; the missing traces do
not prevent testing those hypotheses.
