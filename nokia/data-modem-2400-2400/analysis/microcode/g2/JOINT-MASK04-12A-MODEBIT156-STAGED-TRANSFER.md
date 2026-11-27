# Thirteen-bit receive capture with a timed U14-to-U3 transfer

The prior twelve-bit capture replay counted four U14 latches but did
not honor their **two shared-enable pairs**. The [SN74LS75 datasheet](https://www.ti.com/lit/ds/symlink/sn74ls75.pdf)
shows two latches per enable. Directly taking three first-visit Y bits
and one later Y bit would re-enable a pair at visit 94 and overwrite
one early bit. None of first `3F8` Y5, Y6 or Y7 stays fixed between
visits 46 and 94 across the saved streams (2,648, 3,501 and 6,168
changes among 7,020 symbols). The earlier assignment was a **capacity
count**, not a valid independent-enable schedule.

The [staged-transfer replay](joint_mask04_12a_modebit156_staged_transfer.py)
tests this explicit alternative using photographed U3, U12, U14, U25
and U28 packages:

| Modeled event | Proposed state transfer |
| --- | --- |
| Visit 46, cycle 1,535 | U14 pair A takes first `3F8` Y5/Y6; pair B takes first Y7. |
| Visit 47, cycle 1,554 | U12 takes early row-0 Y0/Y1 and an assumed held mode bit. |
| Visit 93, cycles 3,026/3,039 | U25 FF A takes late row-0 Y2; U3 takes second `3F8` Y7/Y4/Y6 **and copies U14’s first Y7 Q**. |
| Visit 94, cycle 3,071 | U14 pair B is reused for later `3F8` Y4/Y7; U3 retains the transferred first Y7. |
| Visit 141, cycle 4,575 | U25 FF B takes `3F8` Y6 on its separate clock. |
| Cycle 5,000 | Candidate U28 four-bit phase/dibit register loads after all thirteen inputs are held. |
| Cycles 6,000/12,000 | Assumed first and second RxC samples read the held dibit bits. |

U14’s paired enables and U25’s independent flip-flop clocks are package
capabilities, not traced Nokia connections. The model assumes the U14
output reaches one spare U3 D input before U14 pair B is overwritten.
It also moves the earlier proposed U28 load from cycle 4,500 to 5,000:
425 modeled cycles follow the late capture and 1,000 precede the first
RxC. A short real-PROM held-`81`, constant-ADC run shows why U25 storage
matters: `3F8` Y is 127 at cycle 4,575 and changes to 40 at `3F9` on
cycle 4,576. The raw Y bus cannot simply be read at cycle 5,000.

Across 108 saved real-PROM/controller streams and 7,020 symbols, the
proposed staged storage reproduces every direct thirteen-bit state.
Using visit-141 Y6 gives a connected 156-state phase graph with zero
transition conflicts. This is a development graph: the 0.95× streams
that exposed the twelve-bit conflict selected this capture bit. The
[exact direct-product search](joint_mask04_12a_modebit156_exact_products.py)
requires eight terms for phase bit 0 in either polarity, five for direct
phase bit 1 and six for its complement on these observed states. Those
counts and witness expressions do not realize the gate network in the
photographed packages.

The pair-enable, transfer, mode, late-capture, gate, U28 load and
RxD/RxC/SYNDET nets remain assumptions. A thirteen-bit decoder was
frozen and challenged below; its package-budgeted gate and serial path
still need tests. C3 and G2 remain active; missing continuity
measurements do not block those experiments.

Source-hashed reports: [staged transfer and short PROM probe](results/joint-mask04-12a-modebit156-staged-transfer.json)
and [exact direct products](results/joint-mask04-12a-modebit156-exact-products.json).

## Fresh nominal-level holdout

The eight/five-product thirteen-bit witness was frozen before a new
[offset-199 real-PROM/controller challenge](joint_mask04_12a_modebit156_gain100_holdout.py)
at nominal receive gain, with new call/answer payloads and mode edges at
symbols 32 and 48. All four runs have zero clipped samples and a modeled
1,000-cycle interval from the assumed U28 load to first RxC. The edge-32
call and answer and edge-48 answer recover 0/64 wrong dibits, exact
modeled line bytes and exact executed-controller payloads. They reach
unseen `03DE` and `1FCC`. The independent reference misses one dibit
per stream (call index 44, answer index 48), so those exact matches are
conditional on the known transmitted bits and circuit assumptions.

The edge-48 call additionally reaches unseen `190C` at symbols 34, 44
and 47. The frozen gate assigns phase 3 there, yielding six adjacent
decision errors and incorrect modeled line/controller bytes. The
[joined diagnosis](joint_mask04_12a_modebit159_nominal_diagnosis.py)
constrains phase **1** at `190C`: phase bit 1 is wrong in the frozen
witness. All 112 streams form a connected 159-state thirteen-bit graph
with **zero conflicts**. A direct eight/five-product cover still exists
on those observed states, but selecting it using offset 199 makes that
run development evidence for the revised gate. Freeze and challenge
another untouched carrier/level fixture before promoting the decoder.

The [nominal holdout](results/joint-mask04-12a-modebit156-gain100-holdout.json)
and [159-state diagnosis](results/joint-mask04-12a-modebit159-nominal-diagnosis.json)
are source-hashed. The late capture, transfer and serial nets remain
untraced; three passing runs do not establish C3 acceptance.

## Fresh higher-gain holdout

The [revised thirteen-bit cover](results/joint-mask04-12a-modebit159-revised-cover.json)
uses the joined 159-state graph, including the offset-199 `190C` constraint.
It retains eight direct products for phase bit 0 and five for phase bit 1.
That offset-199 run is development evidence for this revision. The cover was
frozen before a new [offset-201, 1.15×-gain real-PROM/controller challenge](joint_mask04_12a_modebit159_revised_holdout.py)
with fresh call/answer payloads and mode edges at symbols 32 and 48.

All four runs have zero wrong decisions, exact modeled line bytes and exact
executed-controller payloads. No PCM sample clips, and the assumed U28 load
still precedes the first RxC by 1,000 modeled cycles. The independent
reference misses dibit 35 in both answer runs; the modeled exactness is
therefore conditional on the known transmitted bits and the circuit
assumptions. None of the four runs reaches a state outside the fitted
159-state graph, so this checks new data and higher level, not unseen-state
generalization.

The [source-hashed holdout](results/joint-mask04-12a-modebit159-gain115-holdout.json)
and its [input fixture](results/joint-mask04-12a-modebit159-gain115-fixture.json)
preserve the test. The thirteen-bit state route still assumes U14-to-U3
transfer, U25 late capture, U28 load, the `3EB` mode bit and the RxD/RxC
serial path. The direct-product cover is not yet a photographed-package gate.
Test that gate and serializer under a package budget and seek a fresh fixture
that visits an unseen state; the untraced nets are testable assumptions, not
a G2 blocker or a C3 pass.
