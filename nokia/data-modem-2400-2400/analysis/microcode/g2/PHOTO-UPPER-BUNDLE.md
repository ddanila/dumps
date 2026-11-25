# Upper PROM-to-latch tracks constrain the next field test

The [front-photo overlay](results/photo-upper-bundle/candidate-front-tracks.jpg)
highlights bright copper segments between the U17/U18 PROM pad regions and
the U29/U30 LS374 pad regions. The [reproducible overlay script](photo_upper_bundle.py)
checks the original photograph's SHA-256 and the two connected-component
bounds at a fixed color threshold. The U17→U29 candidate is one visible
track component. The U18→U30 highlight **merges two adjacent tracks** near
the latch pads, so it cannot be treated as one net. Both disappear into dim
pad regions at their PROM ends. Neither overlay establishes an individual
PROM data pin, the corresponding latch input, or any latch-output route to
U8. It is a tracing aid, not continuity evidence.

The U18 bundle makes a high-data-bit source for an upper-slice register field
worth testing alongside the earlier low-bit assumption. The
[field screen](upper_b_photo_bits.py) runs all 24 permutations of PROM U18
bits 4–7 as U8's four B-address bits under the separated-slice instruction
and candidate U8 I4/I6 crosslinks. At Q=5, each real-PROM run supplies 128
zero or `10` bytes at D38E. Both slices retain the earlier branch, ROM and
clock hypotheses.

| Upper B bit source | Tested orders | D38E bytes selected | `39E`/`39F` result under zero and D4=1 |
| --- | ---: | ---: | --- |
| U18 bits 4–7 | 24 permutations | 128 in each run | `0B` / `0B` in every order |
| Earlier U18 bits 1–4 | One comparator | 128 | `39E` changes `1B`→`3B` after startup |

All 24 high-bit orders change the internal state trace between the zero and
D4=1 runs, but none changes the reached candidate output set. This narrows
the **tested high-bit B-field family**; it does not prove the earlier low-bit
field or identify the DAC path. The low-bit case in
[the D-lane screen](INDEPENDENT-SLICE-D-LANES.md) is therefore a useful
counterfactual input-to-ALU path, with less direct support from these visible
upper PROM-to-latch segments. A future photo or continuity check of U30 Q
pins toward U8 B inputs would discriminate the field families; meanwhile
other mapping, timing and output-path experiments can continue.

The [photo record](results/photo-upper-bundle/report.json) preserves the
source hash, threshold, seeds, bounds and limitations. The
[execution report](results/upper-b-photo-bits.json) preserves every bit order,
trace digest, selected-ROM count and output set.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/photo_upper_bundle.py
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/upper_b_photo_bits.py
```
