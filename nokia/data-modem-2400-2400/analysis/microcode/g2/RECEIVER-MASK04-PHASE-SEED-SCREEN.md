# Initial Q selects the receive path; R5 does not fix the 45° case

The [rotated-carrier replay](RECEIVER-MASK04-CARRIER-PHASE-SCREEN.md)
found that the fixed two-dibit readout fails for a 45° carrier rotation.
This [seed screen](receiver_mask04_phase_seed_screen.py) tests whether
changing initial Am2901 Q or R5 can restore it under the same mask-`04`
mapping, ADC stream and four-row condition. Each of seven scenarios runs
**192,047 real-PROM microinstructions**. The Q override is applied to the
**final configured scenario**: the receive scenario builder otherwise
forces Q=`5`, so changing Q only in its input template would be a no-op.

| Initial state | `3F8` ADC visits | Result at ADC visit 47 | Best result over all 375 visits |
| --- | ---: | ---: | ---: |
| Q=`0`, R5=`00` | 0 | Receive path not reached | — |
| Q=`5`, R5=`00` | 6,000 | 10/12 dibit errors | 2/12 |
| Q=`10`, R5=`00` | 0 | Receive path not reached | — |
| Q=`15`, R5=`00` | 0 | Receive path not reached | — |
| Q=`5`, R5=`40` | 6,000 | 7/12 | 6/12 |
| Q=`5`, R5=`80` | 6,000 | 9/12 | 6/12 |
| Q=`5`, R5=`C0` | 6,000 | 9/12 | 6/12 |

Q=`0`, `10` and `15` complete cleanly but end on other program paths
(`12A`, `084` and `1E9` respectively). They do not enter the selected
receive loop, so they are **entry-selector tests**, not in-loop phase
adjustments. With Q=`5`, changing R5 gives three distinct captured-byte
hashes. This is consistent with the executed `3F8` arithmetic's R5
operand, but none of these seeds produces a zero-error two-dibit readout
at any fixed capture visit. The baseline Q=`5`, R5=`00` capture hash and
error counts are checked against the previous carrier-phase report.

The [machine report](results/receiver-mask04-phase-seed-screen.json) has
the entry paths, trace and capture hashes, all tested seeds and source
hashes. The sweep is deliberately bounded; another R5 seed, a
time-varying control, different ADC route or carrier-tracking circuit
could behave differently. C3 remains open. The next photo-compatible
test should model a row-0-qualified latch holding Y's low nibble until
row 3, then locate the symbol-timed output consumer. Reproduce from the
microcode directory with
`python3 g2/receiver_mask04_phase_seed_screen.py`.
