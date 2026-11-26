# Frozen seven-state readout recovers fresh payloads across line levels

The [seven-state rule](JOINT-MASK04-Q05-PHASE-LEVEL-MAP.md) was fitted
to an earlier payload and tested across selectors, but had no genuinely
new decoded data. This [challenge](joint_mask04_q05_fresh_payload_levels.py)
freezes its `5,6→0`, `8,9→1`, `B,C→2`, `D→3` phase labels and the
quadrant-difference-minus-two rule. It offers one previously unused
eight-byte payload in each selector mode through the previously
verified controller-scrambler transform and real-PROM q3/mask-04
transmitter. The `12A` DAC candidate,
Q=0.5 line filter, +6 sample phase and gain calibrated only on the old
zero-run are fixed. Each stream is checked at 75%, 100% and 125%
level, then fed as complementary ADC bytes into a fresh executed
mask-04 receiver and modeled 8251/unchanged 8031 handoff.

| Selector | New payload | Data dibit coverage | Levels with exact 64/64 receive decisions | Exact aligned controller bytes |
| --- | --- | --- | --- | --- |
| `40` | `D3 26 91 4E B8 07 5C EA` | all four values | 0.75, 1.00, 1.25 | same eight payload bytes |
| `60` | `6A D5 02 B9 40 EF 73 1C` | all four values | 0.75, 1.00, 1.25 | same eight payload bytes |

The external known-carrier decoder is also 0/64 wrong in all six line
fixtures. The frozen seven-state rule has **0 wrong and 0 unknown**
among the 32 preamble/pipeline and 32 data decisions in each executed
receiver run. All six recovered eight-byte *scrambled line* streams
match the offered bytes. With the aligned assumed SYNDET pulse, the
modeled 8251/8031 consumes eight bytes without errors or overruns and
descrambles the exact new payload; a one-bit-early pulse yields eight
wrongly aligned bytes, and a one-bit-late pulse supplies only seven.
The controller remains in `AF`, appropriate for these nonzero data.

This is a strong conditional full-chain replay, not a physical C2/C3
pass. The DAC and ADC buses, Q=0.5 analog filter, two-visit latch,
seven-state phase combinator, serializer, RxD/RxC and SYNDET source
are still hypotheses; the phase labels came from earlier known answers.
Next vary carrier start phase and test a photo-compatible logic/clock
route without refitting the rule. G2 stays active.

The [machine report](results/joint-mask04-q05-fresh-payload-levels.json)
records six Tx/Rx trace digests, line/ADC hashes, states, decisions and
controller controls. Reproduce with
`python3 g2/joint_mask04_q05_fresh_payload_levels.py` from the
microcode directory.
