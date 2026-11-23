# Additional cases after local branch entries

The existing local-table heuristic stops at the end of a consecutive run of
BRT words. At three boundaries, the next word begins disconnected executable
code. Treating that body as an additional case is structurally consistent and
produces clean reset-started traces. Enabling all three alternatives reaches
999 of 1,021 used words statically, leaving 22 unresolved.

This tests a limitation of the table-boundary heuristic. It does not recover
the index encoding, prove a table size, or justify adding arbitrary adjacent
words as entries. The earlier two-/three-entry scenarios remain unchanged.

## The three alternatives

The baseline is the site-scoped ROM-call scenario from [ROM-TAIL.md](ROM-TAIL.md).
Only the following local branch-table counts change:

| Dispatch | Existing entries | Added case | Structural behavior |
| --- | --- | --- | --- |
| 036 | 037,038,039 | Index 3 → 03A | Executes 03A–03B before reaching the 03C dispatcher |
| 03C | 03D,03E | Index 2 → 03F | Starts with TSK, joining the shared low-handler body at 040 or 041 |
| 34C | 34D,34E | Index 2 → 34F | Executes an INC, calls 335 then 366, and branches from 352 to terminal-tail entry 07B |

A branch entry consumes one instruction before jumping elsewhere. The added
cases instead execute bodies of differing lengths. This is why counting only
consecutive branch instructions may understate a dispatch range. It remains
possible that these bodies have another, undiscovered entry mechanism.

The 03F alternative was already tested in the older low-handler study. This
comparison retains that history and evaluates its interaction with the newer
ROM-call ranges and the other two boundaries.

## Independent and combined comparisons

Each of the eight combinations has a separate scenario and graph calculation.
All static explorations finish without stack exceptions. Each scenario then
runs 128 seeds × 1,000 sequencer cycles from reset; all 1,024 runs are clean.
No local entry injection, stack repair or microinstruction rewrite is used.

| Added cases | Static words | Dynamic words in the fixed suite |
| --- | --- | --- |
| None | 993 | 939 |
| 03A only | 994 | 939 |
| 03F only | 994 | 939 |
| 34F–352 only | 997 | 941 |
| 03A and 03F | 995 | 939 |
| 03A and 34F–352 | 998 | 941 |
| 03F and 34F–352 | 998 | 941 |
| All three | 999 | 941 |

Changing table cardinality changes random-number consumption and later choices.
Consequently, the dynamic difference is not just the newly reachable words.
With all cases enabled, the suite gains 03A,03E,03F,34F–352 relative to the
baseline sample but loses 037,03D,046,338,339: seven gained, five lost, net two.
The lost words remain statically reachable. Every report records both sets.
Coverage is not used to rank physical plausibility.

## Recorded executions

In the combined scenario, seed 27 selects index 3 at 036 and reaches 03A,
then selects index 2 at 03C and reaches 03F. Seed 84 selects index 2 at 34C
and reaches 34F. Its trace enters 335 through the call at 350, returns to
351, and calls 366. The common control-flow continuation reaches the tail.

Complete 1,000-record traces for those two seeds are stored once each;
individual alternative reports retain their own dispatch records and excerpts.
All indices remain scenario supplied. The table shape is not supported by an
independent hardware selector measurement, and these sequencer traces do not
identify the arithmetic or physical I/O purpose of the cases.

## Still disconnected

Under the combined candidate, the remaining 22 words are:

`0FA, 0FD–0FF, 256–258, 287–28A, 2CF, 2D9–2DF, 3BD–3BF`.

They retain the unresolved status from the prior catalog. Some fragments
reference one another, but no incoming edge from the reset-reachable graph
has been established. Their presence is not explained merely by calling them
unused code. The full plan remains incomplete.

## Reproduce and verify

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/third_case_study.py \
  --out /tmp/nokia-local-cases
```

[Configuration](third-case-search.json), [summary](results/third-case-study/summary.json),
[combined scenario](results/third-case-study/scenario-all_cases.json),
[seed-27 trace](results/third-case-study/all_cases-seed-27/trace.jsonl), and
[seed-84 trace](results/third-case-study/all_cases-seed-84/trace.jsonl) preserve
the inputs and results. All 27 artifacts reproduce byte for byte. The existing
58-test functional/assumption suite passes. Static and dynamic stack checks
cover each alternative independently; no coverage is merged across them.
