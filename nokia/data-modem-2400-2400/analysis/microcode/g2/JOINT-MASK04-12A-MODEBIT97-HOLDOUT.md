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
