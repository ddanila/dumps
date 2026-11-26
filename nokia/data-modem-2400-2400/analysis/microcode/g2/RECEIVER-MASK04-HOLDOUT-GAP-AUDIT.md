# Executed receive bytes at two long-stream decision gaps

The [fresh long-stream pair union](RECEIVER-MASK04-LONG-PAIR-UNION.md) left
two +7 Hz data dibits undecided: symbol 60 at 75°, where both 46/93 and
47/94 abstained, and symbol 32 at 165°, where those pairs disagreed. This
[gap audit](receiver_mask04_holdout_gap_audit.py) reruns exactly those two
1,152,047-word real-PROM streams, checks that both trace and ADC hashes
match the saved holdout, and captures executed `3F8` Y and `3ED` row bytes
at 25 visits per symbol. It saves the target symbols and two neighbors on
each side, along with the complementary ADC byte selected at every visit.
The decision tables stay frozen; six predeclared visit pairs are scored
without adding reference labels.

| Target | 46/93 `3F8` Y | 47/94 `3F8` Y | 94/141 `3F8` Y | Frozen-readout result |
| --- | --- | --- | --- | --- |
| +7 Hz, 75°, symbol 60 | `FF/7F` | `7F/1F` | `1F/5F` | First two pairs abstain; 94/141 returns the correct `00` dibit. |
| +7 Hz, 165°, symbol 32 | `1F/1F` | `1F/7F` | `7F/CF` | 46/93 returns correct `01`; 47/94 returns wrong `00`; 94/141 abstains. |

The two baseline pair metrics reproduce the previous holdout exactly.
At symbol 60, later ADC samples expose information not resolved by either
early pair. But 94/141 makes **7 wrong decisions and 11 unknowns among 95**
on that entire 75° stream; it cannot simply replace the earlier capture.
At symbol 32, the disagreement occurs at the transition from the `11`
preamble to data. The 46/93 pair sees Y `1F/1F`, while 47/94 sees `1F/7F`;
the latter's wrong label is a real conflict rather than missing table
coverage. The later 94/141 and 140/187 pairs abstain at that boundary.

These results narrow the next question to a **symbol-time selection or
confidence signal** that can choose among executed samples. They do not
identify one. The `3F8` gate and U12 latch remain photo-compatible
hypotheses, while the symbol clock, selector, decision logic and
RxD/RxC/SYNDET path are untraced. Do not add a special case keyed to
symbols 60 or 32 or treat the saved holdout as independent after using it
to choose a rule. A candidate selector should be derived from executed
state or plausible board logic, frozen, then challenged on a new seed.
C3 remains open.

The [machine report](results/receiver-mask04-holdout-gap-audit.json) has
the raw captured bytes, ADC samples, pair scores and source hashes.
Reproduce from the microcode directory with
`python3 g2/receiver_mask04_holdout_gap_audit.py`.
