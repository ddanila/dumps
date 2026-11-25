# A second `3F8` visit resolves the observed transition collisions, with five unseen cases left

The [full-byte capture](receiver_mask04_multivisit_capture.py) reruns the
eight intermediate-angle receive streams with the real PROMs and retains
executed `3F8` Y and row-0/row-3 `3ED` Y at ADC visits 47 and 94 of each
symbol. All eight trace digests, ADC hashes and visit-47 four-bit codes
match the prior failed [intermediate-angle screen](RECEIVER-MASK04-FOUR-BIT-PHASE.md).
The new capture therefore examines the same fixture at a second executed
time, 47 ADC visits later.

A [three-bit phase rule](receiver_mask04_three_bit_two_visit.py) derived
from those eight traces uses `3F8` Y6/Y7 at visit 47 and Y7 at visit 94.
Its phase high bit is visit-94 Y7; its low bit is 1 when all three input
bits agree. It decodes all **376/376 development dibits**. Frozen on a
new random stream, it makes no errors at eleven of thirteen 15°-spaced
carrier angles, but misses **9/16 data dibits at 45°** and **5/16 at
135°**, plus one 135° preamble dibit. The compact phase rule is not an
all-angle receiver.

The [feature audit](receiver_mask04_multivisit_feature_audit.py) then
tests *direct dibit transitions* rather than demanding one absolute phase
label for each symbol. Across the eight intermediate development traces
and thirteen later traces, it compares 987 consecutive-symbol decisions.
The three-bit input has four conflicting transition keys. Four bits per
symbol are the smallest subset of the eight `3F8` high-nibble bits from
visits 47 and 94 that makes the **987 observed transitions
non-conflicting**. Two subsets survive; the
[frozen transition test](receiver_mask04_four_bit_transition.py) uses
visit-47 Y6/Y7 and visit-94 Y6/Y7. These are executed arithmetic outputs,
not raw reference samples.

| Frozen rule on a third, new random stream | Result over 13 carrier angles |
| --- | ---: |
| 86 observed development transition keys | 86/256 possible four-bit-state pairs |
| All measurable preamble and data decisions | **0 wrong, 5 unknown / 611** |
| Data decisions only | **0 wrong, 5 unknown / 208** |
| Angles with unknown data transitions | 0° (1), 135° (2), 165° (2) |

The five unknown data decisions have distinct unseen transition keys
`D9`, `E8`, `7B`, `FC` and `3C`; the test does not fill them from their
known reference answers. The [three-bit report](results/receiver-mask04-three-bit-two-visit.json),
[transition report](results/receiver-mask04-four-bit-transition.json),
and [feature report](results/receiver-mask04-multivisit-feature-audit.json)
retain the raw selected bytes, decisions, trace digests and source hashes.

This finds where the real-PROM receive loop preserves information needed
for phase decisions. The 86-entry readout is an **external diagnostic**,
not a traced logic network or a DSC microinstruction. Capturing two visits,
remembering the previous symbol, mapping transitions to dibits, serializing
two bits and reaching USART-01 RxD all require explicit circuit hypotheses.
The photo shows latch and flip-flop capacity but does not prove these
connections. C3 remains open. The next useful experiment should seek an
executed or photo-compatible small consumer of these visit-47/94 Y bits,
then use fresh streams and the controller zero-run signature to test it.
Missing continuity is not a goal blocker.

Reproduce from the microcode directory with
`python3 g2/receiver_mask04_multivisit_capture.py`,
`python3 g2/receiver_mask04_three_bit_two_visit.py`,
`python3 g2/receiver_mask04_four_bit_transition.py`, and
`python3 g2/receiver_mask04_multivisit_feature_audit.py`.
