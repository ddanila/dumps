# Twelve-bit late-Y7 receive phase holdout

The eleven-bit receive phase state failed a fresh 1.10× late-mode-edge
challenge on known-state transitions. Adding the second `3F8` Y7 value
at visit 94 to the prior mode, early/late Y and row-0 capture bits makes
the joined 96-stream phase graph connected with 97 states and zero
conflicts. This feature was selected using the failed offset-189 streams;
the graph is development evidence. Visit-94 Y7 arrives with the
already modeled later Y4 capture, leaving 2,929 modeled microcode cycles
before the assumed first RxC edge. Its physical latch and clock route is
not identified.

The [frozen twelve-bit cover](joint_mask04_12a_modebit97_cover.py) uses
eight direct products for phase bit 0 and five for phase bit 1. It fits
all 97 development labels and 96 saved real-PROM/controller streams.
The terms are a greedy Boolean cover, not a minimum gate proof; no
photographed-package circuit has been assigned to them.

The [fresh offset-191 challenge](joint_mask04_12a_modebit97_gain110_holdout.py)
uses new eight-byte call/answer payloads at 1.10× calibrated receive
level, each with imposed `3EB` mode edges at symbols 32 and 48. All four
real-PROM streams have 0/64 wrong phase-derived dibits, exact modeled
line bytes, exact executed-controller payloads, zero clipping and zero
controller status errors. Edge-32 reaches unseen `ADD`; edge-48 reaches
unseen `42E`, `89D` and `ADD`. For each selector, Tx, PCM and receiver
PC digests match across the two mode boundaries while Rx digests differ.

The independent reference decoder is exact on both answer streams. It
misses call dibits 38 and 51 in both call streams, so the call-side
zero-error claim is a conditional match to the known transmitter bits
and modeled controller handoff, not an independently validated line
decision at every symbol. The Y2/Y7 storage schedule, mode connection,
Boolean gate implementation, DAC/ADC path and RxD/RxC/SYNDET nets remain
assumptions. C3 and G2 stay active. Next challenge another carrier and
level, and build a timed, package-budgeted capture/gate/serializer route
without relying on a spare U12 flip-flop alone for late Y2.

Source-hashed results: [development cover](results/joint-mask04-12a-modebit97-cover.json)
and [fresh holdout](results/joint-mask04-12a-modebit97-gain110-holdout.json).

## Photo-package capacity replay

The [staged-capture replay](joint_mask04_12a_modebit97_staged_capture.py)
tests a specific allocation using storage packages in the
[board inventory](../board/inventory.json): U14 holds three first-visit
`3F8` bits and later Y4, U3 holds three second-visit `3F8` bits, U12
holds early row-0 Y0/Y1 and the assumed mode bit, and U25 holds late
row-0 Y2 and later `3F8` Y7. The two U25 flip-flops have independent
clocks according to the [74LS74A datasheet](https://www.ti.com/lit/ds/symlink/sn74ls74a.pdf),
so the proposed Y2 and Y7 capture edges need not coincide. U12 has a
common clock: this candidate assumes its mode input holds through the
visit-47 row-bit capture. That mode source and hold are untraced.

Across 100 saved real-PROM/controller streams and 6,500 symbols, the
staged state equals the direct twelve-bit state every time, with zero
phase-decision errors. Early row-0 Y0/Y1 do not change between visits
46 and 47, and late Y2 does not change between visits 93 and 94 in
these streams. The final proposed capture occurs at modeled cycle 3,071,
2,929 cycles before the assumed first RxC edge at cycle 6,000. This is
an event-snapshot and storage-capacity replay, not a measured electrical
timing margin or a traced circuit.

Assigning both U25 flip-flops here displaces their earlier **assumed**
previous-phase-memory role. Phase subtraction, Boolean gates and the
RxD/RxC/SYNDET route therefore remain unallocated; actual data and
clock nets to these packages are also unknown. Test another allocation
or photo-compatible timed phase/serializer path without waiting for
continuity measurements. C3 and G2 remain active, and this capture
replay alone does not pass C3.

The [source-hashed staged report](results/joint-mask04-12a-modebit97-staged-capture.json)
can be reproduced from the microcode directory with
`python3 g2/joint_mask04_12a_modebit97_staged_capture.py`.
