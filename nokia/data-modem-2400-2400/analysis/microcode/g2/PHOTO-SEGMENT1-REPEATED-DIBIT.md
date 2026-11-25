# A repeated-dibit stimulus yields 32 consecutive half-turns in the PROM

[ITU-T V.26 ter §2.7.1](https://www.itu.int/rec/dologin_pub.asp?id=T-REC-V.26ter-198811-I%21%21PDF-E&lang=e&type=items)
specifies continuous 180° phase reversals for 32 symbol intervals in
segment 1. At 2400 bit/s, its line-encoding table assigns dibit `11` a
180° phase change. This supplies a sharper target than merely detecting a
half-turn somewhere in a 32-symbol window.

In the [B4 frame-edge replay](PHOTO-FRAME-TOGGLE-EDGE-PULSE.md), the tested
one-byte/four-symbol alignment puts bit-6 changes at symbols 0 and 16.
The resulting phase-offset blocks are 16 symbols long. Under that explicit
alignment, the frame edges **cannot directly supply** segment 1's
every-symbol reversals. Their physical timing and destination remain unknown;
this conclusion concerns the tested direct edge-to-pulse route.

The [separate PROM replay](photo_segment1_repeated_dibit.py) therefore gives
the DSC2847 32 consecutive synthetic `11` dibits using the earlier
four-visit D127 pulse rule (`90` then `B0` for the rest of each 3,000-visit
symbol). It executes 384,256 microinstructions cleanly. Every selected
PC129 ROM byte and ALU Y value is checked against the PROM; the 256-sample
reconstruction also matches the executed trace's selected-bus SHA-256.
The phase offset from an unmodulated `B0` carrier alternates
`128, 0, 128, 0, …` through all 32 symbols. All 12 DAC bus orders that
passed the real-controller data test decode the 30 available aligned
transitions as `11`, with zero errors.

This establishes **capacity of the candidate microcode path** to carry the
segment-1 phase trajectory. It does not identify the controller source of
those 32 repeated dibits, prove the four-visit D127 pulse circuit, choose a
physical DAC bus, or show analog line output. Segment 1 is still open under
C2. The [direct port-01 screen](CONTROLLER-SEGMENT1-STREAM-SCREEN.md) now
shows that the executed scrambled controller bytes do not themselves carry
a 32-identical-dibit run under contiguous two-bit grouping. The
[machine report](results/photo-segment1-repeated-dibit.json)
contains the phase checkpoints, bus decisions, trace digest and source hashes.
