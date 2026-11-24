# Causal explanations for the default graph's 22 gaps

All 22 used words outside the default 999-word graph now have a replay-backed
explanation of which forced jumps prevent their witnessed entry. This is more
specific than a list of alternative traces: the main listing records the
actual path and the default-policy decisions that must differ along it.

The explanation is scoped to the assumption-driven model. It does not identify
the hardware condition selector or prove that the alternative gates form one
safe integrated model. The default graph, its reachability labels and its
existing execution assumptions remain unchanged.

## Witness paths and suppressed fallthroughs

The existing five [reset witnesses](RESET-WITNESSES.md) are replayed in full
before indexing an explanation. For each gap's first visit, the verifier starts
at the last instruction outside the gap set, records the executed path to the
target, and identifies every BRT that the default model forces true but the
witness actually takes false. Each identified transition falls to the following
instruction instead of the default encoded jump target.

| Witness | Root transition(s) | Gap words explained |
| --- | --- | --- |
| q3-masked-ff | 2D8 → 2D9 | 2D9–2DF |
| swapped-qzero-ff | 0F9 → 0FA; 0FC → 0FD | 0FA, 0FD–0FF |
| q2-reentry-fc | 255 → 256 | 256–258 |
| q3-differences-01 | 3BC → 3BD | 3BD–3BF, then 287–28A |
| q2-zero-q | 2CE → 2CF; 2D8 → 2D9 | 2CF, 2D9–2DB |

Some paths need additional suppressed jumps inside the gap. For example, the
2DF witness requires false branches at 2D8, 2DB and 2DE, not just the initial
2D8 entry. The 258 witness additionally needs fallthrough at 257. These details
are retained per word; a root label alone would omit necessary assumptions.

The listing's `entry_policy_explanations` column links each explanation to its
witness ID and mapping, and gives root cycle, complete path, and each forced
jump's default versus actual target. The existing `explanation_status` still
reports the default graph. Hypothetical entry mechanisms and default
reachability remain separate facts.

## Exhaustive counterfactual policy audit

Across the complete witness traces, twelve BRT sites take false tests despite
being unconditional in the baseline:

`0F9, 0FC, 10D, 255, 257, 2CE, 2D8, 2DB, 2DE, 2E4, 2E5, 3BC`.

The audit enumerates all 4,096 subsets. For each selected site it permits both
true and false tests; all other default policies, encoded targets, dispatch
tables and four-entry stack semantics stay unchanged. This is an analysis-only
relaxation, not a new instruction decode or a patched runtime scenario.

Exactly 32 subsets reach all 1,021 used words. There is one minimum subset,
with seven sites:

`0F9, 0FC, 255, 257, 2CE, 2DE, 3BC`.

Removing any one of those sites loses coverage. Static reachability can use
routes different from the recorded witnesses: after allowing the 0FC
fallthrough, conditional 0FD can jump to 2D9; after allowing the 255 fallthrough,
257 can jump to 2DC. Therefore this graph does not need to relax 2D8 or 2DB to
reach those bodies, even though the masked-FF witness uses those fallthroughs.

**Every complete subset also admits a possible stack underflow at 2FF.** None
provides both complete static reachability and a conservative graph without
stack exceptions. The graph allows independent condition outcomes, so this is
not proof that every integrated run fails. The existing clean traces show the
opposite for specific inputs. It does show why enabling missing fallthroughs
and observing full coverage cannot justify adopting the relaxed graph as a
safe default model.

## What this resolves in the plan

For the address-accounting requirement in step 1, the 22 default exceptions
now have causal, instruction-level entry explanations and exact replayed
states. They need not be treated as unexplained bytes or assigned invented
routine names. The annotation count remains 362; explaining an entry policy
does not explain the arithmetic purpose of its target.

The audit does not prove a single full-coverage hardware mapping, safe execution
for arbitrary external inputs, or completion of the whole plan. Condition
qualification at these BRT sites, the 2FF stack context, wider routine meanings,
and the physical I/O relationship remain separate work.

## Reproduce and validate

[Runner](entry_policy_audit.py) and [report](results/entry-policy-audit/report.json)
retain all 4,096 results, the 22 explanation records, witness support, and
source hashes. The standalone witness catalog and main listing embed the same
explanations after replaying all five complete traces. The 97-test suite checks
the multi-branch 2DF explanation, fallthrough targets, the minimal complete
policy, its underflow exception, and unchanged default reachability.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/entry_policy_audit.py --out /tmp/nokia-entry-policy-audit
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/reset_witness_catalog.py
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/program_reading.py
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -p 'test_*.py'
```
