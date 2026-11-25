# The fixed receive gates need more than a capture-phase shift at 45°

The [phase-47 Boolean readout](RECEIVER-MASK04-PHASE47-BOOLEAN-DIBITS.md)
recovered both reference dibit bits at four input levels, but all those
waveforms used the same carrier phase. This [rotation screen](receiver_mask04_carrier_phase_screen.py)
keeps its Boolean gates, dibits, ADC coding and four-row mask-`04` scenario
fixed. It rotates only the reference 1,800 Hz carrier by 45°, 90°, 135° or
180° and runs two seeded streams at each phase. Each of the eight cases
executes **192,047 real-PROM microinstructions** and captures 24,000
proposed `3ED` latch bytes. The independent reference receiver recovers
every rotated stream's dibits.

| Carrier rotation | Errors at the fixed ADC visit 47, two streams | Best errors after screening all 375 visits | Zero-error visit exists? |
| ---: | ---: | ---: | --- |
| 45° | 10/12, 4/12 | 2/12, 3/12 | No |
| 90° | 0/12, 0/12 | 0/12, 0/12 | Yes |
| 135° | 7/12, 7/12 | 5/12, 3/12 | No |
| 180° | 0/12, 0/12 | 0/12, 0/12 | Yes |

This is an **amplitude/phase decision limitation of the fixed external
readout**. A quarter- or half-turn rotation preserves its phase labels in
these traces; an eighth-turn rotation pushes the sampled values between
those labels. Merely choosing another fixed ADC visit does not restore
all twelve decisions in either 45° or 135° stream. The [machine
report](results/receiver-mask04-carrier-phase-screen.json) retains every
visit's error count, the input and capture hashes, and source hashes.

The result does not prove the DSC lacks carrier recovery. The Boolean
readout was inferred outside the microprogram, and the ADC input route,
four-row dispatch, latch and USART-01 RxD path remain hypotheses. A useful
next experiment is to find an executed phase-adjustment/decision consumer
or a photo-compatible carrier-tracking gate, then rerun these same phase
rotations through that candidate. C3 and G2 remain open. Reproduce from
the microcode directory with
`python3 g2/receiver_mask04_carrier_phase_screen.py`.
The [initial-state follow-up](RECEIVER-MASK04-PHASE-SEED-SCREEN.md) finds
that alternate initial Q values leave this receive path, while three
different R5 seeds do not remove the 45° errors. This keeps the search
on a dynamic phase-control or output-consumer route.
