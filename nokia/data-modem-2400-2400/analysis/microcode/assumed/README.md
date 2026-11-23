# Assumption-driven DSC2847 experiment

This implements the software workflow in [the plan](../PLAN.md): reproducible
field analysis, sequencer execution, a bounded datapath-layout search,
integrated execution, and a routine catalog. Results are **runs under declared
assumptions**, not recovered Nokia wiring or verified modem execution.

The existing illustrative runner and strict photo-based board model remain
separate. This runner uses their functional `Am2901` and `X8X02` components and
the original hash-checked PROM loader. No raw dumps or photographs are modified.

## Conditional flag timing

[CONDITION-TIMING.md](CONDITION-TIMING.md) compares current and previous zero
flags at select 0, with random inputs at other selects. In `flags` mode,
`sources` now accepts `random` per select; unconditional transfers still bypass
condition evaluation. Both timings run cleanly, leaving timing unresolved.

## Separated source-bit search

[Q-INDEPENDENT.md](Q-INDEPENDENT.md) broadens source wiring beyond contiguous
fields. Four candidates remove the table arithmetic's Q=0 requirement and
support a conditional shift-until-zero interpretation of 1E9. Nonzero fixtures
pass, while reset-path table inputs still fail to provide independent evidence.

## Caller-state study

[CALLER-STATES.md](CALLER-STATES.md) tests the arithmetic preconditions on
reset paths with four external-input stubs. Nonzero input exposes failures of
the simple rotation interpretation; zero-input agreement is inconclusive.

## Paired arithmetic experiment

[PAIRED-ARITHMETIC.md](PAIRED-ARITHMETIC.md) tests chip-10 ALU-function bits,
carry feedback and conditional meanings for the six four-entry tables. It
records the 3EF register-overlap counterexample and labels output captures as
virtual, with physical I/O still unknown. `inputs.carry` may remain 0/1 or use
an explicit `mapped-or-previous` policy; its field selectors, initial value,
unknown fallback and provenance are recorded in the scenario. Feedback needs
integrated mode and decoded one-bit fields. Summaries count fallback reads.

## Later branch-table experiment

[BRANCH-TABLES.md](BRANCH-TABLES.md) records a separately configured hypothesis
that reaches 55.34% of used words. Optional `branch_tables` entries use the same
base/count/stride/provenance format as computed-call tables and the same index
source. Unlike a call, a branch-table transfer does not push the stack.
`condition.unconditional_requires_direct` defaults to `true` for compatibility
with existing scenarios; `false` lets select-zero BSR/BRT remain unconditional
when bit 17.7 is clear. Static analysis and execution share this rule.

## Register-field study

[REGISTER-FIELDS.md](REGISTER-FIELDS.md) recovers the second register-counting
pattern and searches instruction fields that do not overlap either register
field. It also reports a semantic limitation: the resulting datapath models
cannot distinguish several different dispatch entries. Their additional clean
runs do not establish a correct instruction mapping or external I/O behavior.

## Reproduce

From the repository root, with Python 3 and its standard library:

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/analyze.py \
  --out /tmp/nokia-assumed
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/suite.py \
  --out /tmp/nokia-assumed
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -v
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode/board -v
```

Analysis must precede the suite: it supplies the three candidate mappings.
`--workers` defaults to four local worker processes; `--scale` permits quick
smoke runs, which cannot satisfy full-suite acceptance. The suite executes:

- Three sequencer condition scenarios and random seeds 0–15, one million cycles
  each; select-zero direct transfers remain unconditional.
- Each of three integrated variants for ten million cycles with seed 0 and one
  million cycles each with seeds 1–3.
- Each variant for one million cycles with hypothetical flag-derived conditions.
- Full seed-0 replay for the sequencer and each integrated variant.
- Four diagnostic runs with select zero made conditional everywhere; their
  failures are reported separately from baseline acceptance.

Individual runs:

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/execute.py \
  --mapping nokia/data-modem-2400-2400/analysis/microcode/assumed/sequencer.json \
  --scenario nokia/data-modem-2400-2400/analysis/microcode/assumed/baseline.json \
  --mode sequencer --seed 0 --cycles 1000000 --trace-limit 1000 \
  --out /tmp/nokia-run
```

Use a generated `datapath-N.json` with `--mode integrated`. The cycle limit is
always honored unless an actual model error occurs; repeated state does not
end a run. Trace storage is bounded by `--trace-limit`, plus at most one sample
per direct-call entry. Counters and the incremental transition digest cover the
whole run. A trace limit of zero keeps summaries and routine samples only.

## Configuration contracts

`sequencer.json` names fields using the existing LSB-first bit-list convention;
`!chip.bit` inverts a bit. Each field includes `bits`, `status`, and `evidence`.
Optional `commands` limits a field's interpretation to those command codes.
Fields may overlap: the register-counting hypothesis overlaps condition and
address-source bits. `remaining_raw` retains bits not consumed by applicable
fields, and every listing/trace retains original bytes.

`baseline.json` declares the assumptions shared by the baseline suite:

- Reset PC 000, unknown stack contents, zero initial RAM/Q, zero carry and
  external shift inputs, and current-operation condition flags.
- Conditions: `constant`, `per-select`, `random`, or `flags`; eight polarities;
  an explicit unknown-flag fallback. Previous flags start unknown; the first
  previous-flag read therefore uses that logged fallback. `unconditional_select: 0` fixes direct
  BSR/BRT select-zero transfers; `null` disables that hypothesis.
- Dispatch: constant, sequence, or seeded random indices, modulo each table's
  entry count. A source of `y` or `q` uses the integrated datapath; the baseline
  uses `scenario`. Each site has its own base, count, stride, status, evidence.
- Indirect BRT: words 008, 03C, 109, 26F and 34C have 17.7 clear.
  `indirect_branch` explicitly uses their microword targets as a **stub**;
  alternatives are a constant target or datapath `y`/`q`. Executions count this
  fallback separately. The true address source is not established.
- External reads: reversed chip-10 immediate on non-address words, with an
  explicit zero fallback on address words. Alternatives are constant, table,
  and `am27s31` reads, indexed by decoded D modulo table size. These index and
  timing conventions are scenario hypotheses, not physical connections.
- Writes: an empty rule list by default because no write-enable/address field
  has been recovered. A rule supplies `pc`, `address`, `source` (default `y`),
  `status`, and `evidence`; matching executions emit address/value records.
  No DAC/controller writes are fabricated in the baseline.

The six four-entry, four-word tables are locally supported by POP boundaries.
Calls 07E and 081 use the nearby 08A–099 table as a hypothesis. Calls 21F and
2C4 also use that table **only as explicit stubs**; their true destinations
remain unresolved. All tables can be replaced independently.

The logical stack monitor is separate from the real four-entry circular stack.
It counts both BLT outcomes as pops and flags reads below logical depth zero or
pushes beyond four, even if an old physical slot still contains a value. It
never repairs the stack. An unknown physical slot stops execution. Nonzero
violation counts invalidate clean acceptance even if the run reaches its limit.
Malformed configurations and PROM hash/size mismatches are errors, not stubs.

## Analysis and outputs

`analysis.json` reproduces the 85 must-be-target entries, exhaustive 2,208
contiguous address windows across chip orders/directions/polarities, greedy
single-bit refinement, condition counts, and direct subroutine walks. The
chosen branch mapping scores 33/85. All tied best windows are retained.

The graph explores actual call/loop stack states to depth four, with a 500,000
state budget. Dispatch edges identify their hypothesis/stub provenance.
Unreachable addresses and possible stack failures are separate diagnostics;
conservative reachability is not demonstrated execution.

`search.json` records the bounded datapath search and weights. It searches
reversed residual-bit instruction windows and reversed register-field windows,
including chip 10. It also considers instruction windows with the known
register-count bits removed. Register diversity, common destinations, loop
setup/load patterns, loop shifts, and shared-bit penalties are heuristic
components. Identical A/B fields are excluded by an explicit search prior;
A/B swaps remain distinct candidates. This is not an exhaustive pin-permutation
search and cannot establish hardware identity. All 512 instructions are legal,
so legality contributes no score. Immediate-byte and D-source hypotheses are
held fixed rather than awarded an invented correctness score.

`ranking.json` retains the top alternatives and score components. Candidate
CSVs include human-readable operations. `dynamic-ranking.json` compares clean
execution, coverage, register changes and unknown flags; a model failure is a
veto, while activity alone is not evidence that a layout is correct.

Each run stores its exact mapping/scenario, their digests, ROM hashes, coverage,
edge/address counts, stack diagnostics, assumption-use counters, bounded trace,
I/O records, routine-entry samples, final state and transition digest.
`routines.json` relates structural labels to observed entries and traces. It
does not name multiplication, filters, DAC writes or controller exchanges
without supporting evidence.

## Interpretation limits

The 01E outlier is consistent with an intentional loop entry: 01C calls 01E,
pushing 01D; BLT consumes that return and either enters PLP at 01D or falls
through to 01F. Both paths balance the initial push. This explains the local
structure without changing B0/B9, but remains a hardware hypothesis.

PLAN.md's 39 BSR targets include the zero placeholder of computed calls. There
are 38 distinct **direct** BSR targets: 37 pass the linear balanced-loop walk,
and 01E is the special entry above. The earlier “38 of 39” count included the
placeholder target; the distinction is explicit in the generated report.

Successful long runs alone are weak evidence: many baseline scenarios spend
almost all their time in the select-zero BRT self-loop at 084 or in a short
PLP/BLT loop. Making every select-zero transfer conditional produces unknown
stack reads, so that global alternative is rejected, not silently used to
increase coverage. More precise dispatch/external-entry/condition evidence is
needed before interpreting the rest of the program.

See [RESULTS.md](RESULTS.md) for measured acceptance and remaining work.
