# Frozen 37-code calibrated-gain receive holdout

The [matched-gain challenge](JOINT-MASK04-12A-TWO-BIT-GAIN1-LOGIC.md)
constrained state `05C` and left one conflict-free 37-code phase graph.
This test froze that table before running four new real-PROM/controller
streams at calibrated 1.0× receive gain, with new payloads and carrier
starts `157`/`159`.

| Carrier | Selector | New nine-bit keys | Wrong transitions between known keys | Modeled clipping |
| --- | --- | --- | ---: | ---: |
| `157` | `40` | `005` | 0 | 0 |
| `157` | `60` | `005` | 0 | 0 |
| `159` | `40` | `001`, `041`, `0E5`, `1ED` | 0 | 0 |
| `159` | `60` | `001`, `041`, `0E5`, `1ED` | 0 | 0 |

The frozen table leaves all four full streams unclassified; it does not
claim line or controller bytes for them. Joining them with the earlier
38 streams yields one 42-code graph with zero phase conflicts. The five
new relative labels are `001→0`, `005→1`, `041→0`, `0E5→1`, and
`1ED→2`. Once those labels are added, all four **development replays**
recover exact modeled line and executed controller bytes, including the
carrier-159 call stream whose independent reference decoder missed
three dibits. The replay is not a fresh pass because it uses the same
streams to infer the labels.

The previously frozen 37-state offset-3 sum-of-products predicts four of
the five new labels but assigns `1ED` phase 1 instead of 2. The
[42-state logic screen](results/joint-mask04-12a-two-bit-logic42-screen.json)
shows that a different observed-state cover still needs at least five
products for the first phase bit at the favorable global offsets. Thus
the one-U15 direct-output capacity objection remains, and the specific
37-state equations do not transfer to every new key. All 470 unobserved
nine-bit keys remain unconstrained by this screen.

The raw challenge and its full captures are in
`joint_mask04_12a_two_bit_gain1_frozen37.py` and
`results/joint-mask04-12a-two-bit-gain1-frozen37*.json`. The joined graph
and development replay are in
`joint_mask04_12a_two_bit_gain1_frozen37_audit.py` and its JSON report.
`joint_mask04_12a_two_bit_logic42_screen.py` reproduces the gate screen
and the frozen-cover predictions. Each report records source hashes.

This is evidence for a stable phase relationship over more receive
states, under the assumed ADC, capture, line and serial routes. It is
not yet a physical gate realization or a complete calibrated-gain
holdout. Seek a photo-compatible multistage decision circuit and a
genuinely new frozen-circuit challenge; keep C3 and G2 active.
