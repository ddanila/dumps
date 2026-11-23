# Command/selector-scoped branch address alternatives

The [global branch-bit search](BRANCH-BITS.md) left contextual decoding open.
This follow-up tests B0 and B9 separately within a complete class of direct
transfers sharing command and condition selector. It finds a limited alternative:
clearing B0 for direct BRT instructions with selector 6 reaches 28A, raising
static coverage from 999 to 1,000 words without losing existing reachable words
or introducing a possible stack exception under the fixed scenario.

This is an analysis candidate, not a new default decode. It does not explain
the remaining disconnected roots or identify the physical branch-address mux.
The principal listing and runtime mappings retain their previous assumptions.

## Bounded search

[Configuration](context-branch-search.json) selects the eight nonempty
command/selector classes among direct BSR and BRT instructions. Each class gets
64 signed PROM-bit choices at each of B0 and B9, for 1,024 candidates. Every
other decoded field, dispatch override, and condition assumption stays fixed.
The graph begins at 000 with an empty stack and explores possible conditional
outcomes. No per-address corrections, injected return addresses, or stack
repairs are used.

Of the 1,024 candidates, 500 have no graph exceptions; many of those reach less
code than the baseline. Only 32 clean candidates gain any previously
unreachable word, and every one gains just 28A:

- 26 reach 1,000 words without losing any baseline word.
- Six reach 999 words, exchanging baseline word 340 for 28A.

No candidate in this search provides a clean path to any other unresolved word.
The search changes one class and one bit at a time; it does not rule out joint
changes, other mux controls, additional dispatch targets, or different inputs.

## Why 28A becomes reachable

The representative no-loss candidate uses PROM bit 10.3 for B0 in this class.
It is zero at all five selected transfers, so its effective behavior is to
clear B0. Four targets change:

| Branch PC | Original target | Candidate target |
| --- | --- | --- |
| 0F2 | 28B | 28A |
| 0F5 | 28B | 28A |
| 0FD | 2D9 | 2D8 |
| 284 | 201 | 200 |

The fifth selected transfer already has an even target. 0FD remains unreachable,
so changing its target does not by itself explain that fragment. The retained
unconditional jump at 0F9 still targets 28B. The additional instruction at 28A
then falls through to that same continuation.

Twenty-six source-bit alternatives fit this no-loss result: 25 have the four
changes above, and one leaves the unreachable 0FD target unchanged. Coverage
therefore cannot choose a physical source bit. Constants on this small instruction class
are particularly weak evidence. The report groups gain candidates by their
complete changed-target sets rather than treating every bit token as independent
support for a wiring interpretation.

## Evidence and reproduction

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/context_branch_study.py
```

[Report](results/context-branch-study/report.json) records every changed target,
gained/lost word, state count, and exception. It also contains a shortest path
from reset to 28A for a no-loss candidate. The 98-instruction path is replayed on the actual
X8X02 model, matching each next PC and complete live stack. Computed-transfer
targets come only from the existing scenario tables; conditional outcomes remain
scenario choices. This finite witness is not a long integrated datapath run.

The unit test checks that a contextual replacement changes only the chosen
branch bit in the selected instruction class and leaves the original rows and
all other fields intact. The full plan remains incomplete.
