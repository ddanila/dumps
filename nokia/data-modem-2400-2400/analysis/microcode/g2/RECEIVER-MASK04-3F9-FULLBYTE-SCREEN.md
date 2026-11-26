# Full-byte `3F9` transitions fit training but fail independent carriers and buffered line

This [screen](receiver_mask04_3f9_fullbyte_screen.py) tests whether the
two-bit projection failure in the [key audit](JOINT-MASK04-12A-3F9-KEY-AUDIT.md)
can be repaired by retaining more of the executed `3F9` output. It uses
visits 46/93 of the current and preceding symbol, with optional `3FA` Y0.
The diagnostic labels come from independent legal carrier streams; no
buffered-line label enters training or model selection.

Four independent training streams use the same seeded dibits at 45° and
135°: one nominal gain/timing fixture and one at 0.85 gain with a
one-sample ADC offset. Four holdout streams use two different seeds at
the same carrier phases and nominal gain/timing. Their real-PROM trace
and ADC hashes match the earlier carrier screen. The script screens
11 byte projections with Hamming and absolute nearest-vector distances;
conflicting exact training vectors abstain. It selects the model with
the most known holdout decisions, then fewest wrong decisions. Because
the holdout chooses the model, its score is a diagnostic rather than an
unbiased final accuracy estimate.

| Captured feature | Training wrong / unknown | Independent holdout wrong / unknown |
| --- | ---: | ---: |
| Current full `3F9` pair, absolute distance | 0 / 27 of 44 | 8 / 34 of 44 |
| Previous + current full `3F9` pair, absolute distance | 0 / 0 of 44 | 9 / 0 of 44 |

The second rule is the coverage-selected candidate. On the saved
ROM-sensitive `12A` buffered-loopback records it gives **8 wrong / 0
unknown of 31 call** and **16 wrong / 0 unknown of 31 answer** data
dibits. One data symbol per stream is excluded because the saved audit
does not include its preceding full-byte pair. Of the eight earlier
no-correct-readout gaps, it gets call indices `8,14,29` wrong and answer
indices `12,13,17` wrong; answer indices `10,31` are correct. It therefore
does not complete the controller's eight-byte receive handoff.

Using the previous symbol is necessary for a DPSK-style decision and
removes exact-vector conflicts in this small training set, but 40
distinct transition vectors among 44 training examples make a lookup
fit weak evidence of a circuit. The independent and buffered errors
reject this nearest-vector rule under the stated fixture. Next inspect
the executed arithmetic and ROM operands that produce `3F9`, and test
a circuit-like differential decision using those states, including gain
and timing changes on fresh legal streams. Keep the DAC/ADC/output pins
as explicit assumptions and C3/G2 open.

The [machine report](results/receiver-mask04-3f9-fullbyte-screen.json)
records all streams, hashes, candidate scores, selected predictions and
buffered gaps. Reproduce with
`python3 g2/receiver_mask04_3f9_fullbyte_screen.py`.
