# Testing the BRT gate with integrated datapath flags

*Runs under the [shared assumptions](ASSUMPTIONS.md).*

The [static gate search](UNCONDITIONAL-GATES.md) used freely chosen conditional
outcomes to expose new paths. This [runtime study](gate_runtime_study.py) uses
the same composed gate and dispatch tables, but lets the integrated datapath
supply the branch conditions. It compares matched reset runs with and without
the gate. No branch outcome is supplied per PC.

## Explicit runtime option

A scenario may now declare this optional field inside `condition`:

```json
"brt_unconditional_gate": {
  "clauses": [["10.2", "!18.7"], ["!10.6", "!11.0"]],
  "status": "hypothesis",
  "evidence": "Composed structural candidate; address-bit correlation is not wiring evidence."
}
```

Each clause is an OR of signed raw PROM bits; all clauses must be true to
retain unconditional status. The gate applies only to BRT instructions that
would otherwise be unconditional. BSR behavior and all initially conditional
instructions are unchanged. A false gate sends the instruction through the
existing condition source, timing and polarity logic. In this study that
means select-zero BRT tests the previous ALU zero flag with inverted polarity.

The runner validates provenance, nonempty clauses and physical PROM-bit names.
Omitting the option preserves existing behavior. The graph and integrated
runner share the same classifier, and a regression test verifies that the
runtime option reproduces the graph candidate's complete state/edge result.
Another test executes a real fallthrough at 0F9 while confirming that the
call at 01C remains unconditional.

## Matched experiment

The study runs 8,192 executions: two mappings (q2 and fitted_original), two
policies (baseline and gated), all eight global dispatch indices, and all 256
default input bytes. Every execution starts at reset with RAM/Q zero and runs
for 256 cycles. The early waits at 117 and 106 receive D followed by zero,
with the last reply held; all other reads remain D. These are diagnostic input
stubs, not recovered board transactions.

Both variants use the dispatch tables from the static search's combined-case
scenario, including its extra local-case entries. Before running, the script
checks complete graph equality with the static baseline and candidate. It
therefore compares the gate within the same structural assumptions, rather
than inadvertently omitting paths through older tables. Previous-flag and
logical-carry policies are retained from the existing integrated scenario.

The report distinguishes the first changed branch decision from the first
changed next PC: a branch whose target is its fallthrough address can change
its test result without changing the execution path. It also records each
first encounter with a relaxed BRT, checks its test against the actual preceding
zero flag, and records final state, visited words and execution digest for
every run. Nonterminal results are described at the 256-cycle bound; the study
does not classify a timeout as an infinite loop.

## Results

All 8,192 executions complete without model or stack errors. Each table row
contains 2,048 runs per policy. The visited-word counts are unions across those
runs, not the coverage of a single continuous execution.

| Mapping | Baseline terminal runs | Gated terminal runs | Paths changed | Baseline visited union | Gated visited union |
| --- | --- | --- | --- | --- | --- |
| q2 | 1,028 | 1,283 | 256 | 506 | 489 |
| fitted_original | 769 | 1,027 | 258 | 430 | 492 |

The gate does not uniformly increase coverage: q2 loses visits to some existing
continuations even while reaching new words and terminating more often.

**2D9–2DB are reached in all 512 gated index-2 runs**, across both mappings
and every D byte. The preceding Q-drain return at 1EB leaves its zero flag set.
The gate makes BRT 2D8 conditional, so its actual previous-zero test is false:
execution falls through to 2D9 instead of taking the baseline target 1CD.
It executes 2D9 and 2DA, then branches from 2DB to 07B and eventually reaches
084. These are ordinary reset executions, without injected branch outcomes,
return addresses or register values. The earlier
[tail arithmetic study](TAIL-CONVERGENCE.md) was local; these runs add an
explicit reset-entry hypothesis for its first tail.

**0FA is reached in one additional run:** fitted_original, index 3, D=FF.
The first changed branch is 10D: previous zero from 109 permits fallthrough
to 10E instead of entering 300. Later, zero from 0F8 makes gated 0F9 fall
through to 0FA instead of taking 28B. Under fitted_original, 0FA copies R0
into R2. Both are zero in this witness, so the instruction executes a write
without a register-value delta. 0FC then branches to 078 and the run reaches
084. This is entry evidence, not a demonstrated nonzero use of that copy.

One further fitted_original path changes at index 5, D=FF: gated 10F falls
through to 110 instead of branching to 345. It adds no formerly disconnected
word. Thus the total is 514 changed paths and 513 runs visiting new static
words. The four newly visited words are exactly 0FA and 2D9–2DB. The other
eight words added by the structural gate hypothesis are not exercised here.

All twelve shortest witnesses in the static report require branch 264 to
fall through, whereas the runtime scenario fixes its select-5 condition to
taken. The successful integrated runs above therefore take alternative paths.
This illustrates why a failed replay of a particular shortest witness cannot
establish that no datapath-feasible path exists.

## Scope

This is a bounded test of two datapath mappings, one condition policy, fixed
global indices and simple input streams. Static paths can require different
indices at different dispatches or other input histories. Even a clean run or
more terminal cases would not identify the gate's physical wiring or prove a
useful modem operation. The new option is not enabled in default scenarios,
and the principal listing's unresolved entries remain unchanged.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/gate_runtime_study.py
```

[Configuration](gate-runtime-study.json) fixes every input and gate choice.
The [report](results/gate-runtime-study/report.json) retains all matched runs,
divergences, visited unions, new-word hits and source hashes. The report and all saved traces reproduce byte for byte. Sixty-four full
witnesses cover D=00 and FF at every index under both policies and mappings.
