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

A direct reuse of U3's spare latches does not recover that phase memory
at its proposed visit-93 clock. By then U14's first-Y bits and U12's
early row/mode bits have been replaced by the new symbol, while U3's
second-Y bits and the late captures still hold the old symbol. Evaluating
the frozen gate on that mixed state differs from the preceding symbol's
final phase in **1,268 of 6,400 transitions**, across all 100 streams.
The first mismatch is symbol 36 of the low-gain selector-40 stream. This
rejects the direct same-gate U3 sampling route under the tested schedule;
it does not rule out another register, a separately held phase signal or
a different clock allocation. Continue those alternatives as experiments.

The [source-hashed staged report](results/joint-mask04-12a-modebit97-staged-capture.json)
can be reproduced from the microcode directory with
`python3 g2/joint_mask04_12a_modebit97_staged_capture.py`.

## U28 phase and dibit pipeline hypothesis

The photographed U28 is marked `74LS169AN`. A [TI LS169-family datasheet](https://www.ti.com/product/SN74LS169B)
describes a four-bit counter with synchronous parallel load. The
[U28 pipeline replay](joint_mask04_12a_modebit97_u28_phase_pipeline.py)
uses that capacity as a **candidate register**: Q A/B hold the current
phase for the next symbol's subtraction, while Q C/D hold the two dibit
bits for serial readout. At an assumed cycle-4,500 load, combinational
inputs use the old Q phase to form the new dibit and the captured twelve-bit
state to form the new phase; all four Q outputs update together. The load
is 1,429 modeled cycles after the final capture and 1,500 before the first
assumed RxC sample. The second sample at cycle 12,000 precedes the next
symbol's load at cycle 16,500, so both output bits remain stored through
their respective sample edges.

On the same 100 saved real-PROM/controller streams, the candidate register
produces **0/6,400 decision errors and 0/13,000 serial-bit errors**. A
cycle-3,000 load, before the late captures, yields 2,991/12,800 bit
errors; a cycle-6,500 load, after the first RxC edge, yields 1,569/6,400
first-bit errors. The first symbol uses the known preamble dibit. These
controls distinguish the event schedule, not the real board clock.

This allocation avoids using U25 as previous-phase memory. It also uses
U28 as a register rather than the earlier assumed serial selector. The
physical U28 load/data/output nets, phase-subtraction gates, bit-select
mux, RxC and SYNDET routes are untraced, and the twelve-bit Boolean cover
has not been realized in the photographed gate budget. The result is a
working timing and storage hypothesis, not a complete receiver circuit or
C3 pass. Test a package-budgeted subtraction/selector and a fresh
carrier/level fixture next. The [source-hashed report](results/joint-mask04-12a-modebit97-u28-phase-pipeline.json)
is reproduced with `python3 g2/joint_mask04_12a_modebit97_u28_phase_pipeline.py`.

The later [level challenge and capture screen](JOINT-MASK04-12A-MODEBIT102-LEVEL-SCREEN.md)
finds twelve-bit state conflicts at 0.95× and places the two surviving
extra-capture hypotheses after this assumed U28 load. The U28 pipeline
remains a timing/storage candidate for the earlier twelve-bit state,
not a receiver implementation validated across those levels.
