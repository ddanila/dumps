# The three saved capture pairs cannot complete the `12A` loopback by selection alone

The [ROM-sensitive buffered-line replay](JOINT-MASK04-12A-BUFFERED-LINE.md)
left data decisions wrong or unknown in each of three frozen receiver
capture pairs. This [gap audit](joint_mask04_12a_readout_gap_audit.py)
compares their saved decisions at each of the 32 data dibits. It asks
whether **any** of the three supplies the correct whole dibit, without
fitting a selector to the answer.

| Selector | No correct known dibit from any pair | All three unknown | Only known label wrong | Correct/wrong conflicts elsewhere |
| --- | --- | --- | --- | --- |
| Call `40` | `8, 14, 29` | `8, 29` | `14` | `15, 16, 19` |
| Answer `60` | `10, 12, 13, 17, 31` | `17, 31` | `10, 12, 13` | `1, 2, 6` |

A selector choosing one whole dibit from fixed pairs `46/93`, `47/94`
and `94/141` cannot recover all eight line bytes in either mode: there
is no correct choice at three call and five answer dibits. The four
all-unknown positions especially require another executed feature,
capture timing or decision rule. At the conflict positions, a selector
must also reject a known wrong label.

This is an information bound on those saved **dibit-level** readouts,
not on bit-level recombination, other DSC outputs or a phase tracker.
The labels are the offered controller data and are used here only to
audit prior holdout results. The next runnable test is to capture `3F9`
and `3FA` Y around the four all-unknown symbols while also collecting
independent legal training streams, then freeze a new rule before
testing these loopback symbols. The photo-compatible latch, serial
clock and RxD path stay assumptions; C3 remains open and G2 active.

The [machine report](results/joint-mask04-12a-readout-gap-audit.json)
records every gap, conflict, byte index, serial bit positions, and the
source report hash. Reproduce with
`python3 g2/joint_mask04_12a_readout_gap_audit.py`.
