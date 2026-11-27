# Twelve-bit receiver level challenge and late-capture screen

The frozen twelve-bit receiver gate had passed fresh 1.10× offset-191
streams. An [exhaustive direct-product search](joint_mask04_12a_modebit97_exact_products.py)
then showed that, on the 97 development states and the 100 states after
that holdout, phase bit 0 needs seven products and phase bit 1 needs five
in separate direct sum-of-products form. The first seven-product witness
mislabels the newly observed `42E` state; a different seven-product
witness fits all 100. This is a Boolean bound on observed labels, not a
photographed-package circuit or a minimum multistage network.

The revised seven/five-product witness was frozen before a new
[offset-193, 1.05× real-PROM challenge](joint_mask04_12a_modebit100_exact7_holdout.py).
Both controller selectors and mode edges were run with new payloads.
There was no clipping, and the independent reference had zero dibit
errors in all four runs. The witness failed on unseen state `2DE`: 6, 4
and 6 wrong dibits in the edge-32 call, edge-32 answer and edge-48 call
runs, respectively; the edge-48 answer passed. The modeled line and
executed-controller payloads failed in the same three cases. The
[diagnosis](joint_mask04_12a_modebit101_gain105_diagnosis.py) shows that
the **new five-product phase-bit-1 witness**, not the seven-product
phase-bit-0 witness, gives phase 2 instead of 0 at `2DE`. The original
eight/five-product gate passed all four runs through the modeled serial
receiver and executed controller. The joined graph was connected and
conflict-free at 101 states; an alternative seven/five direct cover
still exists. The offset-193 result therefore rejects that particular
five-product witness, not the seven-product lower bound.

Combining the seven-product bit 0 with the older five-product bit 1
reproduced the 101-state graph and repaired offset 193, but that choice
was made after seeing the failures. The mixed cover was frozen before a
second [offset-197, 0.95× challenge](joint_mask04_12a_modebit101_mixed_holdout.py)
with new payloads and both mode edges. It failed every stream: 6 and
10 wrong dibits per selector at each boundary, with incorrect modeled
line and controller bytes. The original eight/five-product gate fails
at **the same indices** and has identical phase outputs on these runs.
There is no clipping; the independent reference is exact for selector
`40` and misses dibit 49 for selector `60`. The failure is therefore a
state/timing alias under the tested assumptions, rather than a choice
between these Boolean covers.

Joining all 108 real-PROM/controller streams gives 102 twelve-bit states,
one connected component and **218 directed phase conflicts**. The
[one-bit screen](joint_mask04_12a_modebit102_gain095_feature_screen.py)
tests 76 additional `row0` and `3F8` bits at visits 46, 47, 93, 94 and
141. Only visit-141 `3F8` Y4 or Y6 removes every conflict, yielding
connected 176-state and 156-state graphs, respectively. Both are
development hypotheses selected using offset 197; neither has a frozen
decoder or untouched holdout.

The visit-141 `3F8` value occurs at modeled cycle 4,575, leaving 1,425
cycles before the assumed first RxC. The earlier U28 parallel-load
candidate loads at cycle 4,500, too early to include this bit. U3's
shared latch cannot simply be re-enabled at visit 141: its assumed
second-visit Y7, Y4 and Y6 inputs change between visits 93 and 141 in
5,244, 3,099 and 4,498 of the 7,020 tested symbols. Test a later U28
load with an explicit data-hold route, or separate storage for the
visit-141 bit, before freezing a thirteen-bit gate. The actual clocks,
data nets, phase logic and RxD/RxC/SYNDET path remain assumptions; C3
and G2 stay active.

Source-hashed reports: [exact direct products](results/joint-mask04-12a-modebit97-exact-products.json),
[1.05× holdout](results/joint-mask04-12a-modebit100-exact7-gain105-holdout.json),
[unseen-state diagnosis](results/joint-mask04-12a-modebit101-gain105-diagnosis.json),
[0.95× holdout](results/joint-mask04-12a-modebit101-mixed-gain095-holdout.json),
and [late-bit screen](results/joint-mask04-12a-modebit102-gain095-feature-screen.json).
