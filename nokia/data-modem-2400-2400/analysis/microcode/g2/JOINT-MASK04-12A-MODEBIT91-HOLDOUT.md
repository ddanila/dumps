# Eleven-bit receive phase cover: level transfer and late-mode limit

The ten-bit mode-conditioned receiver fails at higher modeled input levels.
A screen of 92 saved real-PROM/controller streams found that adding late
row-0 Y2 at visit 93 yields a connected 91-state phase graph with zero
conflicts. The [frozen Boolean cover](joint_mask04_12a_modebit91_cover.py)
fits those states and all 92 development streams. It uses 11 direct
products for phase bit 0 and six for phase bit 1; this is a greedy cover,
not a photographed-package circuit or a minimum gate proof.

The late Y2 value is stable through visit 94, but differs from the early
visit-47 value in 3,144/5,980 saved symbols. The existing staged model
uses U12 LS175's common clock for early Y0/Y1. Its fourth flip-flop alone
cannot capture the later Y2 while preserving those early outputs. A
separate latch or timed transfer is required under this hypothesis; the
photos have not identified those nets. The modeled row-0 visit-93 time is
cycle 3,026, before the assumed first RxC edge at cycle 6,000, but the
electrical path delay is unmeasured.

The frozen cover then ran on new controller-derived payloads at carrier
offset 187 and 1.25× calibrated receive level. Both selectors under
edges at symbol 32 and 48 recovered all 64 dibits, exact modeled line
bytes and exact executed-controller payloads. Independent reference
decisions were exact in all four runs. The answer streams clipped twice;
the call streams did not. The paired Tx, PCM and receiver PC digests
match across mode boundaries, while Rx digests differ. Every eleven-bit
state in those four runs had already appeared in development, so this
[holdout](joint_mask04_12a_modebit91_highgain_holdout.py) checks new
transitions and data, not unseen-state extrapolation.

A second [frozen holdout](joint_mask04_12a_modebit91_gain110_holdout.py)
used new payloads and carrier offset 189 at 1.10×, with no clipping and
zero independent reference errors. The edge-32 call and answer runs
reached unseen `73E` and `7F6` and recovered all dibits and controller
bytes. The matched edge-48 runs reached those states plus `13E`, but
each missed four dibits and produced wrong line and controller bytes.
Three of each run's wrong transitions join **known** eleven-bit states;
for example, `536→0C8` requires a different phase step than its frozen
labels allow. The [diagnosis](joint_mask04_12a_modebit91_gain110_diagnosis.py)
finds 132 directed conflicts in the joined 96-stream graph. Relabeling
the unseen state cannot repair this fixture.

An 80-bit follow-up screen on all 96 streams finds 13 individual extra
captures with zero graph conflicts. Visit-94 `3F8` Y7 is one connected
97-state candidate that can be tested at the existing late-Y capture
time; visit-141 row-0 Y4 gives a connected 96-state candidate with less
modeled time before RxC. These are development hypotheses. Next freeze
one candidate and test untouched level, carrier and mode-boundary data,
then construct and time a photo-compatible storage/gate/serializer route.
C3 and G2 remain active.

Source-hashed results: [91-state cover](results/joint-mask04-12a-modebit91-cover.json),
[1.25× holdout](results/joint-mask04-12a-modebit91-highgain-holdout.json),
[1.10× holdout](results/joint-mask04-12a-modebit91-gain110-holdout.json), and
[failure/feature diagnosis](results/joint-mask04-12a-modebit91-gain110-diagnosis.json).
