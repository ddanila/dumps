# Measured results

**Latest experiment:** [independent lookup-ROM targets](ROM-DISPATCH.md)
reach 91.97% under declared site/bank hypotheses; the baseline below is historical.

**Later experiment:** [local branch tables](BRANCH-TABLES.md) improve runtime
coverage to 55.34% with clean runs. The measurements below describe the original
baseline, preserved for comparison. Overall research acceptance remains unmet.

The software workflow is implemented, but **the overall research acceptance
criteria are not met**. Long runs are clean under the declared assumptions;
coverage and identification of the actual datapath remain unresolved.

| Stage | Observed result | Acceptance |
| --- | --- | --- |
| Static field analysis | Command histogram, 85 required targets and 33/85 address score reproduced; all 1024 words listed | Reproduction passes; only 338/1021 used words statically reachable under these assumptions, with 683 explicitly listed unresolved |
| Sequencer suite | 19 runs × 1,000,000 cycles, no stack violations or unknown-stack stops | Long-run criterion passes; aggregate 294/1021 = 28.7953% coverage misses 90% |
| Datapath search | Three named layouts retained; top two are tied A/B swaps | Bounded hypotheses supplied; insufficient evidence to identify Nokia's layout |
| Integrated suite | Three variants × (10,000,000 + 3 × 1,000,000) cycles, plus three 1,000,000-cycle flag scenarios | All requested cycles complete cleanly; stable traces do not establish useful algorithm execution |
| Program reading | Direct-call routine catalog, loop-entry explanation, first-entry trace samples | Structural annotations delivered; arithmetic/filter/I/O identities unresolved |

The fixed suite totals **61 million cycles**. Full seed-0 replays add 31 million
cycles and match summaries and transition digests for all four replayed runs.
No stack contents are synthesized or repaired. No baseline run exceeds the
four-entry limit. The static graph explores 453 distinct PC/stack states without
hitting its exploration budget.

The 01E anomaly has a consistent local interpretation: the call at 01C supplies
the stack entry consumed by BLT at 01E. The two outcomes lead to the PLP at 01D
or to 01F. This does not require a different B0/B9 mapping. There are 38 direct
BSR targets, 37 passing the ordinary linear balanced-loop walk; PLAN.md's total
of 39 included zero, the placeholder address of computed calls.

The common seed-0 run visits 130 used words (12.73%). It then spends almost all
its cycles at the unconditional BRT self-loop at 084. Other condition scenarios
can remain in short PLP/BLT loops. Thus a million-cycle run is not equivalent
to a million cycles of newly understood program behavior.

Four recorded diagnostic runs make select zero conditional everywhere. They
fail after 63, 62, 104 and 124 completed cycles, respectively, with unknown-stack
reads at 1E5, 12B, 089 and 089. This rejects that global alternative under the
remaining assumptions. It does not prove the default condition wiring.

The retained layout scores are heuristic, not probabilities. The top pair
shares one instruction field and swaps A/B, scoring 89.3506; the third uses a
different instruction field, scoring 88.5064. All three run cleanly with
scenario-driven conditions. The tested flag-source hypotheses each cover only
43 words (4.21%); they do not discriminate the layouts. Register changes are
recorded in `dynamic-ranking.json` and must not be mistaken for known arithmetic
semantics. No actual I/O control field has been recovered, so baseline I/O logs
are intentionally empty. Configured external read/write behavior is exercised
by unit tests.

## Evidence and reproduction

- [Analysis](results/analysis.json), [listing](results/listing.csv),
  [control flow and unresolved addresses](results/control-flow.json).
- [Search ranking](results/ranking.json), [dynamic comparison](results/dynamic-ranking.json).
- [Fixed-suite acceptance](results/suite.json), [rejected diagnostic](results/diagnostics.json).
- [Routine catalog and trace excerpts](results/routines.json).
- [Commands and configuration contracts](README.md).

The functional/assumption suite passes 24 tests; the existing strict board suite
passes 18. Tests cover arithmetic, sequencer semantics, PROM evidence,
context-dependent fields, ranking alternatives, dispatch, polarity, replay,
bounded traces, stack failures, unknown flags and external I/O. The strict board
model still correctly refuses to execute unknown hardware wiring.

## Remaining research

1. Explain the 683 statically disconnected words, especially whether execution
   can begin at externally supplied entries or depends on a different address
   source. The current reset-only graph must not label these words explained.
2. Resolve the five indirect BRT words (008, 03C, 109, 26F, 34C), currently
   using explicit microword-target stubs. Recover the destinations of computed calls 21F and 2C4; their 08A table
   assignments are explicit stubs. Establish the index source for all dispatches.
3. Test narrower condition-source/polarity alternatives against stack and
   routine evidence. Do not randomly relax every unconditional transfer.
4. Anchor instruction/register fields with stronger PROM invariants or the
   optional hardware checks, then revisit loop arithmetic and I/O annotations.

These are unresolved findings, not hidden runtime failures or claims of modem
boot. The checked-in scenarios and reports make further hypotheses directly
comparable to this baseline.
