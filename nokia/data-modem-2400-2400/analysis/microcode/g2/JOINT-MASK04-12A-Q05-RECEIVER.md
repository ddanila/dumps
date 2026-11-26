# The improved `12A` line still needs a DSC receive decision path

The [Q=0.5 analog holdout](JOINT-MASK04-12A-ANALOG-HOLDOUT.md) found
a fixed `12A` line setting that the independent known-carrier decoder
reads exactly on new nonzero data. This [replay](joint_mask04_12a_q05_receiver.py)
uses the first new eight-byte payload in each selector mode, checks the
transmitter trace and PCM hashes against the saved holdout, then passes
those samples as complementary ADC input through the real-PROM mask-04
receiver. Both receiver runs sustain the selected visits. The external
reference decoder remains **0/64 wrong** in each mode.

| Frozen external readout | Call wrong / unknown data dibits | Answer wrong / unknown data dibits |
| --- | ---: | ---: |
| 46/93 | 0 / 27 | 0 / 22 |
| 47/94 | 10 / 11 | 4 / 13 |
| 94/141 | 3 / 18 | 2 / 14 |
| ADC-margin selector | 11 / 3 | 5 / 6 |

None reconstructs the 32 data dibits, so none supplies a complete
eight-byte input to the modeled USART/8031 handoff. Across all four
rules, call indices 23, 25 and 27 and answer indices 4, 13, 19, 23,
26 and 28 are unknown. A selector among these frozen rules alone
cannot fill those positions; a new executed feature or decision route
is required. The earlier line-level reference error is therefore not
the cause of this readout gap on these two fresh streams.

The [later key audit](JOINT-MASK04-Q05-RECEIVE-KEY-COLLISIONS.md) found
that the primary 46/93 four-bit feature collides on these data, while
an alternate four-bit capture at the same visits forms four consistent
phase states. Its [frozen phase rule](JOINT-MASK04-Q05-PHASE-STATE-HOLDOUT.md)
recovers both second-payload holdouts and reaches the modeled 8031
handoff. The failed frozen rules above remain useful controls; the
new phase rule is still an external circuit hypothesis.

The DAC, filter, ADC timing and receiver input path remain labelled
photo-compatible assumptions. The readouts are external rules and the
board's RxD wire is untraced. C3 remains open and G2 active. The next
experiment should test a multi-sample consumer at the executed
`3F9`/`3FA` and RAM-return sites, or a distinct photo-compatible
serial output route, against fresh legal payloads.

The [machine report](results/joint-mask04-12a-q05-receiver.json)
contains the hashes, readout indices and receiver trace digests.
Reproduce with `python3 g2/joint_mask04_12a_q05_receiver.py` from
the microcode directory.
