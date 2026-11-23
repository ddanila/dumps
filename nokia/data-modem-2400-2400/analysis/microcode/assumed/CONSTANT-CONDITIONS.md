# Reachability with fixed condition inputs

The integrated scenario's constant condition inputs exclude 215 words from the
optional gated graph, but **none of its 12 newly reachable words**. Thus a
conflict in an earlier shortest witness does not establish that its target
requires different condition stubs. Alternative paths exist.

This study reuses the scenarios, dispatch tables and optional gate from
[GATE-RUNTIME.md](GATE-RUNTIME.md). It constrains conditional tests according to
the scenario, leaving datapath flags and dispatch entries free. Under its
flags mode, selects 1, 4 and 6 are false and select 5 is true. Selects 0, 2, 3
and 7 remain unconstrained unless the unconditional-transfer rule applies.
That rule takes precedence over both polarity and fixed test inputs.

| Graph | Free conditional tests | Fixed scenario inputs | Stack states |
| --- | ---: | ---: | ---: |
| Default BRT policy | 999 words | 783 words | 1,088 |
| Optional composed BRT gate | 1,011 words | 796 words | 1,229 |

Both constrained graphs finish without unused-word visits, stack exceptions or
budget exhaustion. Each contains all words visited by the corresponding
integrated runtime sweep, checked separately for q2 and fitted_original.
These counts are bounds under the declared assumptions, not executed coverage.

The gated constrained graph adds 13 words to the default constrained graph:
0FA, 287–28A, 2CF, 2D9–2DB, 2E5 and 3BD–3BF. There are no losses.
2E5 was already reachable in the original free-condition default graph; the
other 12 are the gains identified by the earlier structural gate search.

The report saves a shortest reset path for each of these 13 words. Every path
is replayed through the actual X8X02 model with matching next PCs and live
stacks, using exactly the same allowed tests as graph exploration. For the
12 previously added words, the new paths use true at 264. Paths to 3BD–3BF
also use false at 208. These agree with the constant stubs, unlike the earlier
free-condition shortest witnesses.

This does not prove integrated feasibility. The graph still allows each ALU
flag test and each dispatch entry to vary independently. In the existing
integrated sweep, actual flags reached only 0FA and 2D9–2DB among the 12 new
words. The remaining gap calls for studying flag and dispatch dependencies,
not rejecting those words solely because of a conflicting shortest path.
The default runtime, default graph and curated annotations are unchanged.

## Reproduce

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/constant_condition_study.py
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -p 'test_*.py'
```

The [report](results/constant-condition-study/report.json) records reached and
excluded words, runtime subset checks, replayed paths and source hashes. The
two scenario snapshots and report reproduce byte for byte. All 77 tests pass,
including false skip/loop behavior, unconditional precedence, fixed-source
polarity and default-graph preservation.
