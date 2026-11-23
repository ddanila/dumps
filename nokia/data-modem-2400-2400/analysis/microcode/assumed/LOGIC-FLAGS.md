# Defined logical flags remove a carry-feedback assumption

An explicit Am2901B flag model removes unknown logical carry/overflow values
from the functional datapath. Four fitted reset examples remain clean with
their existing condition policies, dispatch and external-input stubs. Unknown
carry-feedback substitutions fall from 19–21 per 1,000-cycle run to zero.
One example changes its intermediate loop behavior; none gains a new final
state or establishes continuing modem operation.

## Component equations and connection scope

[AMD document 01566B, page 5-8, Figure 9](https://pccomponents.com/datasheets/ADVAN-AM2901BDMB.pdf)
defines logical-operation carry and overflow pins. They are not necessarily
zero, even though carry-in does not affect the logical F result.

With bitwise P=R OR S and G=R AND S, the implemented rules are:

- OR: carry is NOT(all P bits) OR carry-in; overflow equals carry.
- AND: carry is any G bit OR carry-in; overflow equals carry.
- NOT-R AND S uses the AND rule with complemented R.
- XOR uses the OR rule with complemented R.
- XNOR uses the equivalent recurrence `c[i+1] = !P[i] OR (!G[i] AND c[i])`.
  Overflow is the XOR of carries entering and leaving the highest bit.

The eight-bit functional mode cascades the two slices' carry normally and
uses the high slice's overflow. This connection remains an explicit model
assumption, not recovered Nokia carry-lookahead wiring. Active-low P/G pins
and physical timing are outside this change. The downloaded scan's hash is
recorded in [logic-flags.json](logic-flags.json); the PDF is not copied into
the repository.

## Opt-in behavior

Historical runs keep logical pins unknown. A scenario enables the new model
through a provenance-labelled input policy:

```json
"logic_flags": {
  "mode": "am2901b-ripple",
  "status": "hypothesis",
  "evidence": "AMD 01566B Figure 9; ordinary carry cascading assumed"
}
```

This belongs in `inputs` and requires integrated execution. Omitting it, or
using the explicit `unknown` mode, retains the historical behavior. At the
component level, the corresponding option is `Am2901(logic_flags=True)`.
No existing mapping or fitted condition policy is silently rewritten. The
separate clocked board model retains its documented logical-flag limitation.

## Reset comparisons

Each historical 1,000-cycle example is rerun first and checked against its
archived transition digest. Only then is the new flag policy added.

| Profile | Words before / after | Unknown carry substitutions before / after | First control-flow difference |
| --- | --- | --- | --- |
| Original roles, zero input | 162 / 162 | 19 / 0 | Cycle 144 at 1EA |
| Original roles, marked input | 187 / 187 | 21 / 0 | None |
| Swapped roles, zero input | 186 / 186 | 20 / 0 | None |
| Swapped roles, marked input | 186 / 186 | 20 / 0 | None |

All four runs have equal final PC/stack/RAM/Q to their historical counterparts.
Their flag traces differ, and the zero-input original-role case has an
observable intermediate data and branch effect:

| Cycle / PC | Historical unknown flags | Defined flags |
| --- | --- | --- |
| 139 / 1C2 | Carry unknown | Carry 1 |
| 140 / 2D0 | Feedback substituted with 0; Q becomes FF | Feedback 1; Q remains 00 |
| 143 / 1E9 | Q shifts to 3F | Q remains 00 |
| 144 / 1EA | Repeats at 1E9 | Exits to 1EB |

The earlier first carry-input difference is at cycle 89, PC 1E0; the table
shows the local chain leading to the first Q and control-flow differences.
Thus the previous unknown-flag fallback was not merely cosmetic. The test
does not refit selectors to obtain this result, and it does not establish
their hardware meanings.

The real-decision audit finds no unknown condition flag consumed in any of
the four new short traces. Initial previous flags are still unknown before
the first operation; the new model does not invent their power-on values.

Two additional million-cycle runs, original roles with zero and marked input,
finish cleanly with maximum stack depth three and no unknown carry feedback.
They reach 162 and 187 words and finish at 1EC and 084 respectively. These
long runs check stability; they do not turn the remaining loops into useful
signal-processing work or increase the earlier sequencer coverage.

## Verification and reproduction

The component tests exhaust all 2,560 combinations of two four-bit operands,
carry-in, and the five logical functions against expanded Figure 9 equations.
XNOR is checked with the separately expanded carry and overflow formulas,
rather than repeating the implementation's recurrence. Another 810 boundary
cases compare the eight-bit model with two separately executed four-bit
slices. Existing exhaustive byte arithmetic and default-unknown tests remain.
Scenario tests check provenance, mode restrictions, and removal of an actual
unknown-feedback read. All 64 functional/assumption tests pass.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/logic_flag_study.py \
  --out /tmp/nokia-logic-flags
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -p 'test_*.py'
```

The [report](results/logic-flag-study/report.json), four short trace directories
and two bounded long-run trace directories retain exact scenarios, mappings,
summaries and I/O logs. All 31 result files reproduce byte for byte. The full
plan remains incomplete: disconnected entry mechanisms, physical I/O and
broader algorithm interpretation still need evidence.
