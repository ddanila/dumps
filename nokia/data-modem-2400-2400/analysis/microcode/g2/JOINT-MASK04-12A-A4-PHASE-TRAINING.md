# The controller's A4 rate pattern can train the conditional receive-state map

The 32-symbol constant preamble in the [half-quadrant replay](JOINT-MASK04-12A-PHASE-TIMING.md)
holds one receive state for all 33 captures. It leaves all 64 possible
four-state phase labelings (after fixing a global rotation) compatible
with the preamble. Fitting the subsequent payload would leak its known
answers into the decoder.

The unchanged 8031 emits the V.26 ter segment-2 GPC pattern in its
`40`-selector A4 stream, as independently checked against the standard
in the [controller comparison](CONTROLLER-SEGMENT2-PATTERN.md). This
experiment packs that exact 64-bit window, beginning at bit 1 of the
first A4 byte, into eight LSB-first line bytes:
`FC 03 7C 0E 0E F8 C0 18`. It offers only those known bits to the
real-PROM q3/mask-04 transmitter. The bus-0 DAC candidate, Q=0.5
line, +6 sample phase, zero-run-fixed gain, complementary ADC route
and executed receiver are held fixed. As in the half-quadrant test, a
one-time `20` R1 offset is applied at the start of the muted interval.

The A4 receiver produces exactly the state family `2,6,9,D` seen in
the earlier fresh-payload replay. Among all 64 possible labelings
anchored at `2→0`, **one** decodes all 32 known A4 dibits:
`2→0, 6→3, 9→1, D→2`. This map is learned from A4 alone. Applied
unchanged to the already saved fresh-payload call and answer receiver
states, it recovers **64/64 dibits in each**, all eight line bytes per
mode, and the exact decoded payloads
`D3 26 91 4E B8 07 5C EA` and
`6A D5 02 B9 40 EF 73 1C` in the aligned modeled 8251/unchanged
8031 handoff. Both handoffs consume eight bytes with zero errors and
overruns. No fresh-payload label was used to choose the A4 map. The
external fixed-carrier reference decoder makes two errors at the end
of the A4 training stream; that does not enter the DSC phase fit.

This is a stronger conditional acquisition witness, not a physical C3
pass. The A4 bits are independently established, but this fixture
reuses a synthetic A3 interval and a diagnostic R1 phase intervention;
it does not execute an uninterrupted controller A4-to-payload session.
The phase-labeling logic, ADC/latch timing, serial route and SYNDET
source are still photo-compatible assumptions. Next run the actual
controller A3/A4 timing and a subsequent data stream through one
uninterrupted DSC transmit/receive fixture, and test a plausible
hardware or microcode phase-normalization mechanism without fitting
to payload answers. C2/C3/G2 remain open and active.

The [machine report](results/joint-mask04-12a-a4-phase-training.json)
records the source hashes, real-PROM trace digests, A4 states, unique
training map and both modeled controller holdouts. Reproduce from the
microcode directory with:

```sh
python3 g2/joint_mask04_12a_a4_phase_training.py
```
