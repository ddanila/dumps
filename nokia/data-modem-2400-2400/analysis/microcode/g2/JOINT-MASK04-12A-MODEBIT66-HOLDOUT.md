# Mode-bit phase graph and fresh matched-mode challenge

The assumed `3EB` mode bit removes the phase conflicts found in the
nine-bit receiver state, but the first frozen Boolean decoder does not
generalize to a fresh moving-mode run. This is a useful constraint on the
candidate connection, not a G2 blocker.

[`joint_mask04_12a_modebit66_graph.py`](joint_mask04_12a_modebit66_graph.py)
adds the imposed mode bit at visit `46` to the nine captured state bits in
66 saved real-PROM/controller streams: 49 with an `81→A1` edge at symbol
32, 13 with held `81`, and four with an edge at 48. The resulting 61-state
graph is connected and has zero directed phase conflicts. The otherwise
comparable later-Y6 graph has 60 states in two components. Exact
sum-of-products bounds require six or seven direct products for phase bit 0,
depending on polarity, more than one four-arm U15 output provides.

[`joint_mask04_12a_modebit66_cover.py`](joint_mask04_12a_modebit66_cover.py)
freezes a Boolean phase cover that fits all 66 development streams. It is a
logic hypothesis, **not** a photographed-package circuit. The fresh
[`holdout`](joint_mask04_12a_modebit66_holdout.py) uses new eight-byte call
and answer payloads at carrier offset 177. It runs the real PROMs with the
same executed 8031 transmitter, PCM and PC path under held `81` and an
`81→A1` edge at symbol 32. A modeled aligned 8251/8031 handoff checks
recovered line bytes and descrambled controller payloads.

| Assumed mode | Call dibit errors | Answer dibit errors | Line/controller bytes |
| --- | ---: | ---: | --- |
| Held `81` | 0/64 | 0/64 | Exact in both |
| Edge at 32 | 16/64 | 15/64 | Wrong in both |

The paired Tx trace, PCM and PC digests match across modes for each selector;
the Rx traces change as intended. All 31 wrong transitions in the edge runs
touch a state absent from development. The
[`diagnosis`](joint_mask04_12a_modebit66_diagnosis.py) combines the four
challenge streams with the 66 development streams: its 64-state graph stays
connected with zero conflicts. Of the three new states, only `32D` has a
wrong frozen phase label: the joined graph requires phase 3 under the chosen
global offset, while the frozen cover emits 2. The held runs also visit new
`0C2` and pass. These four streams are now development data for any revised
decoder; another untouched carrier/payload challenge must test that revision.

The mode schedule, its connection to the phase logic, DAC/ADC and latch nets,
and RxD/RxC/SYNDET timing remain assumed. A successful follow-up would
support this conditional receive model, but it would not by itself establish
the physical Nokia circuit or pass C3. The next bounded test is to freeze a
revised `32D` phase label, then challenge new held and moving-mode streams
while checking package gate capacity and timing separately.

Source-hashed machine results:
[`graph`](results/joint-mask04-12a-modebit66-graph.json),
[`cover`](results/joint-mask04-12a-modebit66-cover.json),
[`holdout`](results/joint-mask04-12a-modebit66-holdout.json), and
[`diagnosis`](results/joint-mask04-12a-modebit66-diagnosis.json).
