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

## Frozen revision and independent offset-179 challenge

[`joint_mask04_12a_modebit70_revision.py`](joint_mask04_12a_modebit70_revision.py)
freezes exactly that correction: phase bit 0 is ORed with the exact ten-bit
state `32D`. It fits the resulting 64-state, 70-stream development graph
without changing any other observed label. The
[`new challenge`](joint_mask04_12a_modebit70_holdout.py) uses untouched
eight-byte payloads at carrier offset 179, with matched held-`81` and
edge-at-32 runs for each selector. All four have 0/64 wrong dibits, exact
modeled line bytes, exact executed-controller payloads, zero controller
status errors and zero clipped samples. The held runs reach unseen `099`;
the moving-mode runs reach unseen `2D9`. The old cover would have made
13/64 and 16/64 errors on those moving-mode runs, so the correction was
actually exercised.

Within each selector, the held and moving-mode runs have identical Tx, PC
and PCM digests and different Rx digests. This supports a mode-conditioned
receiver decision under the stated stimulus. The exact-state correction
adds logic to a cover that already exceeds one U15 output's four direct
arms; a photographed-package implementation, actual `3EB` mode net and
serial/line timing have not been established. C3 remains open. Next, test
a package-budgeted multistage gate and a pin-compatible mode-to-serializer
route using the same frozen decision function, then vary mode boundary,
gain and carrier phase on untouched data.

The [package-delta audit](joint_mask04_12a_modebit70_package_delta.py)
compares this function with the earlier photographed-package nine-bit
circuit. They agree on 60 of the 64 observed revised states. At `01C`
and `11C` in held mode, both old phase bits must be cleared; at `12D`
and `32D`, phase bit 0 must be set. The shortest direct decodes for
those two correction groups use four and five input literals,
respectively, on the observed state set. The old circuit alone makes
13/16 dibit errors in **each** held/moving offset-179 selector pair;
the revised function makes none. The existing network already uses all
three U19 NANDs and the U15 AOI output. Photographed U7 has one
eight-input NAND, while U13 has four inverters and U21 one NOR left
under that allocation. This identifies the extra gate work but does
not claim a complete package-budgeted overlay or measured timing.

## Fresh late-boundary control

The [offset-181 boundary challenge](joint_mask04_12a_modebit70_late48.py)
holds new call/answer transmitter payloads, PCM and receiver PC paths fixed
while moving the imposed `3EB` `81→A1` edge from symbol 32 to 48. The frozen
64-state decoder makes 0/64 dibit errors in each of the four real-PROM
streams. All four recover exact modeled line bytes and executed-controller
payloads, with zero clipped samples and zero controller status errors. The
edge-48 streams reach unseen `099` and `2D9`; the edge-32 controls reach
unseen `2D9`. Within each selector, Tx, PCM and PC digests match while Rx
digests differ. The modeled interval from visit-94 capture to the first RxC
edge remains 2,929 cycles in all four cases; this is an assumed schedule,
not a measured propagation margin.

This additional mode-boundary holdout strengthens the conditional receive
decision without resolving the gate-resource and physical-net questions.
The next tests should use a different gain/carrier phase and construct a
complete package-budgeted route for the same frozen function.

## Fresh lower-level and mode-boundary control

The [offset-183 low-level challenge](joint_mask04_12a_modebit70_lowgain.py)
uses new call/answer payloads, a new carrier start and a calibrated 0.8×
receive level. It repeats the edge-at-32 and edge-at-48 schedules with the
same frozen decoder. The independent reference has zero wrong dibits in
all four streams. The decoder also has 0/64 wrong dibits per stream and
recovers exact modeled line bytes and executed-controller payloads, with
zero clipping and zero controller status errors. Edge-32 reaches unseen
`225` and `259`; edge-48 reaches unseen `019`, `025`, `19D`, `225` and
`259`. Each selector's paired Tx, PCM and PC digests agree, while its Rx
digests differ with the imposed mode edge. The modeled visit-94-to-RxC
interval remains 2,929 cycles.

This tests a signal level that had exposed earlier phase-gate failures,
but the successful decision still depends on the assumed mode input,
analog/ADC mapping and aligned serializer. A high-level or clipped case
and a complete package-budgeted circuit are next; C3 and G2 stay active.

## Higher-level failure and extra capture bit

The frozen ten-bit decoder fails a fresh [1.25× offset-185 challenge](joint_mask04_12a_modebit70_highgain.py)
at both mode boundaries: 23/64 call and 17/64 answer dibit errors in each
boundary pair, with wrong modeled line and controller bytes. All four
independent reference streams still have zero errors, but each PCM stream
clips twice. Every wrong decoder transition touches a new state. The
[diagnosis](joint_mask04_12a_modebit70_highgain_diagnosis.py) joins these
four streams with the 70 development streams and finds a connected
70-state graph with zero conflicts. Four new labels disagree with the
frozen rule: `02E/22E` need phase 3 instead of 2, and `108/308` need
phase 0 instead of 1. These offset-185 streams are now development data.

A matched [1.15× control](joint_mask04_12a_modebit70_gain115.py) also
clips twice per stream and misses 23/17 dibits. Its call-side independent
reference misses one dibit, so it is not an exact-reference holdout.
The [1.05× edge-32 control](joint_mask04_12a_modebit70_gain105.py) has
**zero clipped samples**, yet the frozen decoder misses 11 call and
10 answer dibits and yields wrong controller bytes. The answer-side
reference remains exact; the call-side reference misses one dibit.
Thus clipping is not required for this decoder failure under the modeled
line path. At 1.15×, the same ten-bit captured states can require
different phase steps: adding its four streams to the 70 development
streams yields 112 directed graph conflicts. A static relabeling of the
ten-bit state cannot repair that gain level.

The [one-extra-bit screen](joint_mask04_12a_modebit70_level_feature_screen.py)
tests 80 captured bit choices across all 92 saved streams. The ten-bit
graph has 82 states and 314 directed conflicts. Six individual extra-bit
choices remove all conflicts; row-0 Y2 at visit 93 or 94 gives a connected 91-state
graph with zero conflicts. The result remains connected and conflict-free
on the 89-stream subset that excludes the three known call-side 1.05×/1.15×
reference-error runs. Row-0 Y2 never changes between visits 93 and 94
in these streams, but differs between the earlier U12 capture at visit
47 and visit 93 in 3,144 of 5,980 symbols. Early row-0 Y0/Y1 also shift
1,723/3,058 times. All four U12 LS175 flip-flops share a clock, so its
spare flip-flop **alone** cannot make the later Y2 capture while its
other outputs retain the early Y0/Y1 values. A separate storage stage
or a timed transfer is an explicit circuit hypothesis to test; the
photographs have not established those nets.

This is a development feature screen, not a working decoder. Next freeze
an eleven-bit phase function and test untouched high-level payloads and
carrier starts, then test its gate/serializer timing. C3 and G2 stay open.

Source-hashed machine results:
[`graph`](results/joint-mask04-12a-modebit66-graph.json),
[`cover`](results/joint-mask04-12a-modebit66-cover.json),
[`holdout`](results/joint-mask04-12a-modebit66-holdout.json), and
[`diagnosis`](results/joint-mask04-12a-modebit66-diagnosis.json);
[`revision`](results/joint-mask04-12a-modebit70-revision.json) and
[`offset-179 holdout`](results/joint-mask04-12a-modebit70-holdout.json),
plus the [`package delta`](results/joint-mask04-12a-modebit70-package-delta.json).
The [late-boundary result](results/joint-mask04-12a-modebit70-late48.json)
records all four new cases.
The [lower-level result](results/joint-mask04-12a-modebit70-lowgain.json)
records the four 0.8× cases.
The [1.25× failure](results/joint-mask04-12a-modebit70-highgain.json),
[failure diagnosis](results/joint-mask04-12a-modebit70-highgain-diagnosis.json),
[1.15× control](results/joint-mask04-12a-modebit70-gain115.json),
[1.05× control](results/joint-mask04-12a-modebit70-gain105.json), and
[extra-bit screen](results/joint-mask04-12a-modebit70-level-feature-screen.json)
record the level limit and the next candidate.
