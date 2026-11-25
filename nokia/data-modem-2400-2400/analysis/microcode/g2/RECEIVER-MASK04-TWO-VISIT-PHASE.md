# A second receive visit resolves one collision, but the fixed rule still misses bits

The [two-visit screen](receiver_mask04_two_visit_phase.py) reruns four
192,047-cycle real-PROM receive traces at 45° carrier rotation. It compares
the executed `3ED` row-0/row-3 pair at ADC visit 47 with a second pair at
offsets −47 through +94 visits. The first two trace digests and visit-47
pairs match the prior [rotated codebook](RECEIVER-MASK04-ROTATED-CODEBOOK.md).
The four reference dibit streams all decode in the independent receiver.

The one-visit pair `(F3,F2)` represents two reference phase states in
these traces. At offset +47, its second row-3 byte separates them in the
inspected data: `F8` for state 0, and `F3` or `F5` for state 1. The
two-visit key has **no conflicting phase labels** across the four streams,
whereas the one-visit key has one. This is a useful data-path clue, not a
receiver proof. A lookup fitted on the first stream at +47 leaves 4/12
decisions unknown on the selection stream and 3/12 and 4/12 unknown on
the next two. Replacing the collision requires a rule that generalizes
beyond memorizing whole pairs.

Using all four inspected streams, a provisional external rule keeps the
seven-state visit-47 lookup and changes `(F3,F2)` to state 0 only when
the +47 row-3 byte is `F8`. It decodes those four streams exactly.
The [frozen-rule replay](receiver_mask04_two_visit_rule.py) then tests
two **new** random streams at 45° and the same streams at 135°:

| Rotation | Fresh stream `4E11` | Fresh stream `6B39` |
| --- | ---: | ---: |
| 45° | 0/12 dibit errors | **2/12** |
| 135° | 0/12 dibit errors | **2/12** |

All 48 fresh decisions are covered. In the failing 45° stream, visit-47
`(F3,F2)` followed by `(F5,FF)` at +47 is another phase state the frozen
override did not recognize; two adjacent dibit decisions are wrong. The
135° failure likewise involves `(F3,F2)` with a different second byte.
So a second visit carries useful information, but this simple fixed
rule does not finish carrier-phase recovery. Further threshold tweaking
on these same streams would be development, not fresh validation.

The phase labels, lookup, previous-symbol subtraction and capture schedule
are external hypotheses. A two-visit consumer needs storage and timing
that have not been traced, and no executed output reaches USART-01 RxD.
C3 remains open. The next test should seek an executed retained-state or
multi-visit decision, then check new random streams and the RxD path.
The [screen report](results/receiver-mask04-two-visit-phase.json) and
[frozen-rule report](results/receiver-mask04-two-visit-rule.json) contain
the pair bytes, scores, trace digests and source hashes. Reproduce from
the microcode directory with
`python3 g2/receiver_mask04_two_visit_phase.py` and
`python3 g2/receiver_mask04_two_visit_rule.py`.
