# Complete executed receive states on the full-byte line candidate

The [frozen row-logic transfer test](JOINT-MASK04-FULL-BUS-ROW-LOGIC-OFFSET.md)
showed that the older reference-waveform Boolean decoder fails even at
zero offset on the selected full-byte DAC/line fixture. This capture keeps
the same two previously recorded non-zero payloads and −7, 0 and +7 Hz
analog cases, but retains the complete `3F8` Y and `3ED` row-0/row-3 Y
sequence at ten predeclared visits in every symbol. All six cases contain
65 symbols and complete 780,047-instruction real-PROM receive runs. Their
PCM, ADC hashes and PROM trace digests match the earlier offset challenge;
the independent reference decoder remains exact.

The [state report](results/joint-mask04-full-bus-receive-states.json) is a
reusable executed-byte corpus, not a decoder. It stores the expected
transmitted dibits for scoring, separately from the received Y bytes.
The DAC/ADC routes, filter, AGC, clock and latch remain labelled model
assumptions. The offset cases were not used to *fit* the direct lookup
below, but they were inspected in earlier experiments, so they are not
a blind holdout for choosing a new feature.

## Direct four-bit transition transfer

The [transfer screen](joint_mask04_full_bus_state_transfer.py) uses the
two existing capture pairs `46/93` and `47/94`. Each state takes Y6/Y7
from each pair visit; a previous/current state transition indexes a
table. Only the two **zero-offset** cases provide table labels. Both
pair tables have zero development-label conflicts, with 18 and 25
observed keys respectively. The unchanged tables are then evaluated
on the four ±7 Hz cases:

| Pair | Call −7 wrong/unknown | Call +7 wrong/unknown | Answer −7 wrong/unknown | Answer +7 wrong/unknown |
| --- | ---: | ---: | ---: | ---: |
| `46/93` | 0/23 | 0/21 | 1/26 | 0/20 |
| `47/94` | 0/28 | 0/26 | 0/26 | 0/22 |

Each cell scores the **32 actual line-data dibits**. Thus the zero-offset
`47/94` table recognizes just 26 of 128 shifted data dibits, although
none of its recognized labels is wrong. The `46/93` table recognizes 38
and gets one wrong. A conflict-free fit on these two development streams
therefore supplies too little coverage for byte recovery under the offset
challenge. The earlier reference-waveform-trained tables cover more
transitions, but their external fallback still fails some offset cases.
These lookup results identify a data-coverage limit, not the Nokia
receiver's phase-tracking algorithm.

Next, use the saved full Y sequences to test a physically motivated,
causal multi-sample feature. Specify its selection and conflict handling
before a **new** payload and initial-phase fixture; do not call the
already inspected offsets independent validation. Test an alternative
ADC/clock route if no Y-only rule generalizes. C3 and G2 remain open.

Run `python3 g2/joint_mask04_full_bus_receive_states.py` and
`python3 g2/joint_mask04_full_bus_state_transfer.py` from the microcode
directory. The [transfer report](results/joint-mask04-full-bus-state-transfer.json)
records table keys, scores and source hashes.
