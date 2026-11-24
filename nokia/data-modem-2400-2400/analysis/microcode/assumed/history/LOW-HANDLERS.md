# Low-address handler dispatch: 75.42% measured coverage

*Runs under the [shared assumptions](../ASSUMPTIONS.md).*

A boundary-derived sparse dispatch hypothesis at 008, plus local tables at
036 and 03C, reaches **770 of 1,021 used words (75.42%)** in reset-based runs.
A matched control using the previous branch scenario and the same 128 seeds
reaches 677 words (66.31%). The new hypothesis adds 93 visited words and loses
none in this experiment. The earlier 55.34% result used only 16 seeds.

This advances control-flow coverage, not physical address-source recovery.
The 90% target, complete routine interpretation and physical I/O identification
remain unmet. Every added target is labeled as a hypothesis in the scenario.

## Evidence and unresolved alternatives

Within 009–058, the script finds boundaries after unconditional branches or
returns, excludes known direct destinations and skip-reachable words, and
separates local dispatch entries. Seven remaining roots are plausible handlers:

`009, 00D, 013, 022, 032, 03A, 054`.

They lie in a region skipped by the old fallback at 008. Several paths join
the tail at 05B and eventually reach 084. This is structural evidence for a
collection of handlers; their commands, arguments and physical caller remain
unknown. It does not prove that 008 selects them. The previous encoded target
300 remains an eighth alternative. Index order is scenario-owned and is not
claimed as recovered command encoding.

At 036, three following words (037–039) are direct select-zero BRT entries.
Treating 036 as local dispatch overrides its probable direct-source bit;
that bit overlaps the register field and is not established for every word.
At 03C, the next two words (03D–03E) are likewise direct branch entries.
03F is a TSK and may be a third entry. It is kept as a separate ablation,
rather than accepted solely for the extra reachable word.

| Static hypothesis, applied cumulatively | Reachable used words | Stack exceptions |
| --- | --- | --- |
| Previous branch scenario | 682 | None |
| Add sparse handlers at 008 | 758 | None |
| Add local table at 036 | 773 | None |
| Add two entries at 03C | 775 | None |
| Weaker third-entry alternative at 03F | 776 | None |

The selected scenario reaches 775 words statically and leaves 246 unresolved.
The unexplained addresses remain listed explicitly in the graph artifact.
Nothing is reclassified as understood merely because it is reachable.

## Execution and verification

Both the selected scenario and matched control run seeds 0–127 for 1,000
cycles each, all starting at reset. The selected scenario has no stack errors
and reaches maximum depth **four**, the hardware limit. It dynamically visits
all but five statically reachable words: 17B–17E and 2A9. No external entry
PCs or stack repairs contribute to coverage. Random-stream consumption changes
with dispatch choices, so this is matched sampling effort, not identical
external stimulus on each path.

A further million-cycle integrated run uses Q-independent mapping 2, seed 1,
and constant external D=55. It completes cleanly and saves register and virtual
output traces. Full million-cycle replays reproduce both that summary/digest
and an archived original-runner summary/digest exactly. The functional/assumption
suite passes 39 tests, including sparse call/branch stack behavior, table
validation, boundary recovery and the third-entry distinction.

The runner and static graph now share `table_targets`: tables may use either
`base/count/stride` or a nonempty `targets` list. Mixed formats, duplicates and
out-of-range addresses are rejected. Both formats require provenance. Existing
regular tables retain their original behavior. Sparse calls push a return
address; sparse branch dispatches do not.

## Reproduce and inspect

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/handler_study.py \
  --integrated-cycles 1000000 --out /tmp/nokia-handler-study
```

Without `--integrated-cycles`, only static analysis and the matched short suites
run. [Configuration](../handler-search.json) contains the region, exclusions and
local table evidence. Outputs include:

- [Boundary evidence](../results/handler-study/boundary-evidence.json) and [scenario](../results/handler-study/scenario.json).
- [Measured coverage and all comparison scenarios](../results/handler-study/summary.json).
- [Selected graph and unresolved words](../results/handler-study/graph-local-03C.json).
- [Annotated 1024-word listing](../results/handler-study/annotated-listing.csv).
- [Integrated run](../results/handler-study/integrated/summary.json).

Computed calls 21F and 2C4 and the branch at 26F still have unresolved address
sources. Several larger disconnected regions remain beyond this handler block;
those are the next targets for structural analysis, not arbitrary entry injection.
