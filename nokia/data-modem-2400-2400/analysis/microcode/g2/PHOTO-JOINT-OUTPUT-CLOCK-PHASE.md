# The candidate transmitter tolerates many DAC sample-clock phases

The [clock-phase screen](photo_joint_output_clock_phase.py) checks all 375
distinct alignments of a hypothetical DAC latch that captures once per 375
`129` visits. It uses the exact D127 sequence and upper-ROM recurrence checked
by the [joined real-PROM run](PHOTO-JOINT-TONE-TRAINING-DATA.md). At offset 0,
the reconstructed full-code SHA-256 must equal the captured PROM trace. The
other offsets are projections of that same checked recurrence, not additional
full PROM executions. The [result JSON](results/photo-joint-output-clock-phase.json)
contains every surviving common offset and the selected offset checks.

| Check | GPC selector `40` | GPA selector `60` |
| --- | ---: | ---: |
| Candidate 2,100 Hz tone peak | 375/375 offsets | 375/375 offsets |
| 0/62 A3→A4 errors on all 12 candidate DAC buses | 258/375 | 257/375 |
| Worst errors on an individual bus at any offset | 2 | 2 |

**234 offsets** give the 2,100 Hz peak and 0/62 errors on every bus in
*both* modes. Thus the joined result does not require precisely the one
offset used in its original trace. Its data-decision score does still depend
on latch phase; the remaining offsets cause one or two errors under the
external matched-filter decoder. The selected candidate bus has the same
`R²(2100)=0.335990` at all offsets, because shifting the capture phase
rotates its periodic code sequence without changing the tone fit.

The arithmetic clarifies what the assumed clock is doing. In the four-word
q3 loop, 375 `129` visits span 1,500 microinstructions. With the photographed
14.4 MHz oscillator and **one oscillator period per microinstruction**, that
is 9,600 samples/s; 3,000 visits per assumed symbol then give 1,200 baud.
The held `88` input advances the phase `56` counts between samples, exactly
2,100 Hz in 256-step phase units at 9,600 samples/s. The `B0` input advances
`208` counts, equivalent to `−48` counts after sampling, whose alias is
1,800 Hz. This is a conditional sampled phase walk. If each instruction
takes `k=2,3,4` oscillator periods while the input pulse schedule stays at
3,000 visits/symbol, the implied symbol rates fall to `600, 400, 300` baud.
The current fixture therefore specifically requires the `k=1` timing family
or a revised input schedule.

No 375:1 divider, latch clock wire, Y-to-74LS273 bus, complete DAC08 bus or
line-side waveform has been recovered. The photo suggests the DAC08 B5←Q4
segment only. The all-phase screen constrains a **possible** clocked output;
it does not identify the clock circuit or satisfy C2. A useful next test is
to screen photographed counter/clock parts and PROM control bits for a
plausible 9,600 Hz latch gate, then replay that explicit gate and the 74LS373
hold possibility against the same continuous PROM trace. Receive and echo
processing remain separate required tests.
