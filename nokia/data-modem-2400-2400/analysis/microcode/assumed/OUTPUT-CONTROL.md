# Output-control patterns remain ambiguous

*Runs under the [shared assumptions](ASSUMPTIONS.md).*

The transient adjustment motivates looking for a Y-output consumer, but the
PROM patterns do not select a unique output enable. A bounded search finds
43 different one-/two-bit predicates that separate the proposed example
groups. All 43 also pass the held-out table groups, yet they activate different
sets of 83–705 used instructions. This is underdetermination, not 43 recovered
hardware strobes.

## Assumed labels and search

The positive training examples are the 32 words of the virtual-output tables
379–388 and 392–3A1. The negative examples are the 32 RAM-transform words
3C5–3D4 and 3DA–3E9, plus the self-branch at 084. The held-out groups are
3AB–3BA (positive) and 3EF–3FE (negative). The two transient first-result
instructions 2D9 and 2DC are additional probes, not training examples.

These labels are assumptions derived from the candidate arithmetic model.
They are not physical I/O observations: RAM writes could coincide with
external writes, and an idle loop could have external side effects. The
held-out groups also repeat related instruction templates, so their agreement
is not independent validation of a signal assignment.

The search enumerates all 64 single literals and 1,984 two-literal conjunctions
over distinct PROM data bits, with both polarities: 2,048 predicates total.
It does not restrict the search to currently unassigned bits, since control
fields could be multiplexed or share signals. No predicate is installed in
the emulator or used to produce claimed DAC transfers.

## Results

| Check | Result |
| --- | --- |
| Fits to training labels | 43 |
| Fits with no smaller fitted literal subset | 24 |
| Distinct activation sets across the used ROM | 43 |
| Fits passing both held-out table groups | 43 |
| Fits selecting both 2D9 and 2DC | 29 |
| Range of activated used words | 83–705 |

Representative alternatives illustrate the ambiguity:

| Predicate | Activated words | Existing interpretation of the tested bits |
| --- | --- | --- |
| 17.5 = 1 | 294 | ALU source I0 and condition-select bit in all four layouts |
| 11.6 = 0 AND 17.3 = 1 | 243 | Destination bit; 17.3 is also a source bit in layout 1 |
| 17.3 = 1 AND 18.6 = 0 | 212 | Source-field bits in some/all retained layouts |

All three also select the two transient-tail probes. Therefore matching those
probes does not distinguish an output-enable interpretation from a pattern
already explained by operand selection or destination control. The report
lists every candidate's instruction addresses, command histogram and field
ownership separately for all four retained layouts.

Only 18.5 is unassigned to any named field in all four complete mappings.
Its value is zero in every training-positive and training-negative example,
so it cannot distinguish these groups on its own. This statement concerns
the present field assignments, including the speculative virtual output-slot
field; it does not mean that 18.5 has no hardware function or that other bits
cannot have context-dependent roles.

## A broader no-load gate

For comparison, the report also evaluates `17.3=1 AND destination=1`, where
destination 1 is the current no-load decode (`11.7=1, 11.6=0, 11.5=0`).
This four-literal gate selects all 48 virtual-table words and both transient
probes, but activates 210 words overall:

| Command | Activated words |
| --- | --- |
| INC | 166 |
| POP | 26 |
| BLT | 15 |
| PLP | 3 |

For example, it also selects the loop-test instruction 1EA. These other
activations are predictions of that gate, not observed writes and not known
false positives. Applying it as an output rule would introduce substantial
unverified behavior beyond the original virtual-output tables.

## Consequence

A unique external-write control cannot be justified from these example groups
alone. The raw-bit alternatives and their differing address sets give concrete
predictions for comparison with future board or protocol evidence. For now,
physical output enable, destination and timing remain unresolved. Existing
explicit virtual captures remain labelled as such, and no new captures are
introduced by this study.

## Reproduce

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/output_control_study.py \
  --out /tmp/nokia-output-control
```

[Configuration](output-control-search.json) owns the example labels and search
scope. The [report](results/output-control-study/report.json) reproduces byte
for byte and retains all competing predictions. The existing 61 functional/
assumption tests pass. No control flow, datapath mapping, I/O model, or reset
coverage result changes.
