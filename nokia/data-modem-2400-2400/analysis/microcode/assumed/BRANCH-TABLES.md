# Local branch-table experiment

A separate scenario increases measured sequencer coverage from 294 to **565 of
1021 used words (55.34%)**. It visits 304 words absent from the original suite;
33 words reached by the old suite are not visited by these fixed seeds under
the new assumptions. The old results remain intact for comparison.

This is evidence for a better control-flow hypothesis, not identified Nokia
wiring. The 90% coverage target remains unmet. Datapath semantics and physical
I/O connections remain unresolved.

## Evidence and changed assumptions

At 109, the old runner decoded a BRT whose presumed address-source bit is clear
and used the encoded value 150 as a fallback. Immediately after it, 10A–111
contains eight consecutive direct, select-zero BRT instructions. Treating those
as an eight-entry dispatch table explains their otherwise disconnected entry
points. The table routes to:

| Index | Entry | Destination |
| --- | --- | --- |
| 0 | 10A | 11A |
| 1 | 10B | 148 |
| 2 | 10C | 18B |
| 3 | 10D | 300 |
| 4 | 10E | 259 |
| 5 | 10F | 345 |
| 6 | 110 | 09E |
| 7 | 111 | 133 |

Similarly, 34C precedes two direct BRT entries: 34D → 361 and 34E → 353.
The new scenario treats this pair as a two-entry table. Whether 34F is an
additional entry or reached by some other mechanism is unresolved; it is not
added solely to increase coverage.

The other change separates condition truth from address selection:
`unconditional_requires_direct: false` makes select-zero BSR/BRT unconditional
regardless of bit 17.7. The bit still distinguishes direct calls from computed
calls. This makes all ten computed calls unconditional too. It does **not**
change TSK or BLT conditions, rewrite the stack, or add external entry points.
Both table indices remain seeded scenario inputs.

## Comparison of the hypotheses

The static analysis explores both outcomes of uncertain conditions with actual
logical return/loop stacks, capped at four entries:

| Hypothesis | Reachable words | Stack exceptions |
| --- | --- | --- |
| Original baseline | 338 | None |
| Table at 109 only | 704 | Possible underflow at 27F |
| Table at 109 + select zero independent of address source | 639 | None |
| Add table at 34C | 682 | None |

The table-only alternative is not accepted merely because it reaches more
addresses. It allows 26F, a computed BRT with select zero, to fall through into
the subroutine at 270 without a return address. The independent-condition
hypothesis removes that path. This supports the combined interpretation, but
does not prove the remaining address-source assumptions.

Exact scenarios for all four comparisons are recorded in the summary.

## Execution results

- Seeds 0–15 each complete 1,000,000 sequencer cycles without model errors,
  stack underflows or stack overflows. Maximum stack depth is three.
- Each of the three existing datapath variants completes 10,000,000 integrated
  cycles with seed 0. Their control-flow coverage remains scenario-driven.
- The primary experiments total 46 million cycles. A further one-million-cycle
  seed-0 replay exactly reproduces the summary and transition digest.
- Static reachability is 682 words; actual aggregate sequencer coverage is 565.
  No externally injected entry addresses or stack repairs contribute to either.
- The first 1,000 cycles already achieve the same coverage for these seeds:
  long execution still spends almost all its time in short loops. This remains
  a limitation, not evidence that the full program has been understood.
- All eight table entries at 109 are represented statically; seven are selected
  dynamically by this seed suite. Only entry 1 at 34C is selected dynamically.
  The annotated listing and dispatch report distinguish these cases.

The original million-cycle seed-0 baseline still reproduces exactly after the
runner changes. The functional/assumption suite passes 26 tests and the strict
board suite passes 18.

## Reproduce and inspect

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/branch_study.py \
  --out /tmp/nokia-branch-study
```

The command reads the checked-in three candidate mappings; it does not rerank
or replace them. `--cycles`, `--integrated-cycles`, and `--workers` support
smaller diagnostic runs; requested and completed lengths are recorded.

- [Scenario](branch-tables.json)
- [Summary and comparison scenarios](results/branch-study/summary.json)
- [Control flow and remaining unreachable words](results/branch-study/control-flow.json)
- [Annotated listing](results/branch-study/annotated-listing.csv)
- [Dispatch destinations and observed execution counts](results/branch-study/dispatch-analysis.json)

The next address-source questions are 008 and 26F, which still use the
microword fallback, and the computed-call targets at 21F and 2C4. Arbitrary
entry injections could inflate coverage, but would not resolve these sources.
The source must remain an explicit hypothesis supported by program structure
or datapath evidence before it replaces the baseline.
