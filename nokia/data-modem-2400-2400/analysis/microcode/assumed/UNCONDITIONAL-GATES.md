# Conditional BRT alternatives expose clean paths to disconnected fragments

*Runs under the [shared assumptions](ASSUMPTIONS.md).*

The assumption that select-zero BRT instructions are unconditional contributes
to the remaining entry gaps. A bounded raw-bit gate search finds four two-bit
alternatives that add paths without graph exceptions. The best single gate
reaches 1,009 used words; a conjunction of two gates reaches 1,011. This is
structural evidence about the assumption, not recovered physical condition
wiring. The default graph still reaches 999 words and retains 22 unresolved
words.

Unlike the earlier [branch-address search](CONTEXT-BRANCH.md), this experiment
changes no target, command, selector, dispatch table or decoded raw field.
It changes only whether an already-assumed-unconditional BRT is restricted to
the taken outcome or is allowed both outcomes. BSR behavior is unchanged.
Conditional outcomes remain free scenario choices, not inferred ALU flags.

## Search and controls

The [study](unconditional_gate_study.py) tests 64 single signed PROM-bit gates
and 3,968 AND/OR gates over two distinct signed raw bits: 4,032 candidates.
A gate value of one preserves the existing unconditional classification; zero
permits fallthrough as well as the existing target. The same Boolean rule is
applied to the whole class, without per-address exceptions. All candidate
fallthrough sets are retained and equivalent sets share one graph evaluation;
there are 1,088 distinct sets.

| Gate class | No exceptions, no new words | No exceptions, gains | With exceptions |
| --- | --- | --- | --- |
| Single bit | 11 | 0 | 53 |
| Two bits | 869 | 4 | 3,095 |

A diagnostic that permits fallthrough at every formerly unconditional BRT
reaches all 1,021 used words, but also reaches unused 1DF and produces numerous
possible stack underflows/overflows. It is not treated as a successful decode.
No target is changed to obtain these paths, and no return address is injected.

## Four clean individual alternatives

Here `!` means bit inversion. Counts include used words only.

| Gate retaining unconditional BRT | Reachable | Added words |
| --- | --- | --- |
| `!10.1 OR !18.7` | 1,007 | 0FA, 287–28A, 3BD–3BF |
| `10.2 OR !18.7` | 1,005 | 0FA, 287–28A, 2CF |
| `!10.3 OR !10.6` | 1,006 | 287–28A, 3BD–3BF |
| `!10.6 OR !11.0` | 1,009 | 287–28A, 2D9–2DB, 3BD–3BF |

All preserve every baseline reachable word, as expected when only additional
conditional outcomes are allowed. For the best individual gate, the newly
conditional BRT sites are 037, 03E, 048, 05C, 10F, 2D8, 2E5, 3BC and 3BF.
For example, fallthrough at 2D8 supplies an entry to 2D9 without inventing a
new computed-dispatch target or changing the address field.

All four gates use bits already participating in the recovered branch address.
In particular, `10.6` and `11.0` are B2 and B0. Their apparent success may
reflect address placement in this particular ROM rather than a real gate.
Coverage alone provides no independent reason to interpret address bits as
condition controls.

## Composed gates and remaining gaps

All eleven combinations of two or more clean gates were also checked. Each
composition retains unconditional status only when all its constituent gates
are true, allowing the union of their fallthrough sets. All eleven remain
free of graph exceptions, and the maximum is 1,011 used words.

A smallest best combination is:

`(10.2 OR !18.7) AND (!10.6 OR !11.0)`

It adds 0FA, 287–28A, 2CF, 2D9–2DB and 3BD–3BF. The ten words still
unreachable under this combination are **0FD–0FF, 256–258 and 2DC–2DF**.
The report records all 21 BRT sites relaxed by this combination, not just the
sites adjoining new fragments. It therefore exposes collateral policy changes
rather than hiding them behind per-entry coverage results.

## Sequencer replay and limits

Forty-three shortest reset-started witness paths cover every newly reachable
word under each individual gate and the representative best composition.
Each path is replayed through the actual X8X02 model, matching its next PC and
live stack at every step. Dispatches use only existing scenario tables. There
are no stack repairs or synthetic return values. A regression test checks
that the override preserves all non-BRT unconditional decisions, adds the
expected paths, leaves decoded rows unchanged and does not alter the default
graph after the experiment.

The graph accepts an optional analysis-only unconditional predicate, and the
witness helper uses the same predicate during replay. Omitting it preserves
the existing behavior. The structural search itself changes no runtime condition policy or default
scenario. The witnesses demonstrate feasible sequencer paths under free
conditions; they do not prove that the datapath can supply those conditions
in sequence. Consequently these are named analysis candidates, not resolved
exceptions in the principal program listing. The plan's reachability gate
remains incomplete.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/unconditional_gate_study.py
```

[Configuration](unconditional-gate-study.json) states the search scope and
[report](results/unconditional-gate-study/report.json) retains every Boolean
candidate, equivalence class, exception, gained word, composed candidate,
replayed path and source hash. Earlier branch-target studies remain unchanged
under the default policy.

A [follow-up integrated study](GATE-RUNTIME.md) now exposes the gate as an
optional scenario setting. With the same dispatch tables and actual previous
flags, it reaches 0FA and 2D9–2DB from reset. Default scenarios remain unchanged.
