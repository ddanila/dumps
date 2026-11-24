# Assumption-driven DSC2847 experiment

[What the program does](PROGRAM-OVERVIEW.md) connects startup, all eight
handlers, shared arithmetic, terminal behavior and the controller-to-DAC
experiment. This synthesis is available for the final acceptance review;
the plan remains open until that review is complete.

This implements the software workflow in [the plan](../PLAN.md): reproducible
field analysis, sequencer execution, a bounded datapath-layout search,
integrated execution, and a routine catalog. Results are **runs under declared
assumptions**, not recovered Nokia wiring or verified modem execution.

The existing illustrative runner and strict photo-based board model remain
separate. This runner uses their functional `Am2901` and `X8X02` components and
the original hash-checked PROM loader. No raw dumps or photographs are modified.

[PLAN-AUDIT.md](PLAN-AUDIT.md) is the current acceptance checklist. The refreshed
execution check passes, while broader routine interpretation remains unfinished. A declared one-way
controller-to-DAC transaction is replayed; its physical routing remains a hypothesis. The historical baseline suite still has its
original failed coverage result. Run `plan_validation.py` for current evidence.

[PROGRAM-READING.md](PROGRAM-READING.md) is the consolidated entry point for
reading the microprogram: a 1,024-word annotated listing, six separate datapath
profiles, evidence-linked routine names, and explicitly unresolved entries.

[LOGIC-FLAGS.md](LOGIC-FLAGS.md) adds an explicit scenario option for the
Am2901B logical carry/overflow equations. Historical scenarios retain unknown
logical flags; the new comparison removes carry substitutions and checks the
effect on fitted reset paths without changing their condition policies.
[DEFINED-CONDITIONS.md](DEFINED-CONDITIONS.md) then refits current/previous
condition sources with the defined flags, replays the local numerical-use
witnesses, and compares their reset extensions without promoting a timing.

## ROM bytes as ALU input

[ALU-FEEDBACK.md](ALU-FEEDBACK.md) tests retained-Y addressing of the actual
lookup ROM. The trace distinguishes sampled bytes from operands selected by
the ALU. All 128 short runs finish cleanly, but the sampled paired-arithmetic
calls still have zero source pairs; this does not establish signal processing.
[OPERAND-PROVENANCE.md](OPERAND-PROVENANCE.md) expands to 128 seeds and traces
last writers, including writes of unchanged bytes. It distinguishes initial
zeros from zeros written by earlier transform entries.
[OPERAND-PATHS.md](OPERAND-PATHS.md) proves that the current control-flow
hypothesis excludes all non-table source writers from paths to these calls,
and identifies routine 341–344 as a concrete decode question.
[PREPARATION-DECODE.md](PREPARATION-DECODE.md) expands the source search and
compares A/B swaps: sixteen layouts retain the old fixtures, but none turns
341 into an operand loader while preserving those same interpretations.
[CALLER-CHAIN.md](CALLER-CHAIN.md) follows preparation through the actual
three-call sequence: the A/B swap loads bytes but loses their tested effects
from final internal state. It does not assume a rotation formula.
[SINGLE-CALLER.md](SINGLE-CALLER.md) follows the separate 18B caller and finds
surviving preparation effects in different internal registers under both
register-role hypotheses. This supplies concrete downstream predictions.
[FIRST-USE.md](FIRST-USE.md) distinguishes unused surviving values from
actual downstream operand uses and records preparation-dependent arithmetic
under one candidate from each register-role hypothesis.
[CONDITION-FIT.md](CONDITION-FIT.md) replays both numerical-use witnesses in
the main runner with consistent previous-flag selectors and explicit PC-keyed
input stubs, replacing the local per-instruction branch choices.
[CONDITION-EXTENSION.md](CONDITION-EXTENSION.md) extends those policies to 512
runs and two million-cycle reset runs. They remain stack-safe, but none
of the reset cases reaches preparation, and some use unknown decision flags.
[SELECTOR-COMPLETION.md](SELECTOR-COMPLETION.md) then varies only previously
unconstrained selectors. Asserting selector 5 reaches preparation from reset
and yields an input-dependent loop under the preserved fitted policies.
[TERMINAL-TAIL.md](TERMINAL-TAIL.md) characterizes the common tail at 078–084
and shows why a blanket fallthrough/restart interpretation is unsupported
by the observed stack contexts.
[ROM-TAIL.md](ROM-TAIL.md) adds a site-scoped ROM-table alternative reaching
2BC–2C5, with explicit overflow counterexamples for unrestricted nesting.
Its graph reaches 993 words; 28 remain unresolved.
[LOCAL-CASES.md](LOCAL-CASES.md) compares additional case bodies at three
local dispatch boundaries. The combined alternative reaches 999 words
statically and leaves 22 unresolved; its table sizes remain hypotheses.
[BRANCH-BITS.md](BRANCH-BITS.md) tests 128 global B0/B9 alternatives against
that graph. None improves reachability; inversion witnesses expose empty-stack
accesses. Context-dependent decoding and other dispatch families remain open.
[FRAGMENTS.md](FRAGMENTS.md) classifies the seven remaining entry families,
rules out unchanged ROM bytes for two roots, and tests a conditional one-unit
ALU adjustment at 2D9/2DC. Local probes do not add reset coverage.
[TAIL-CONVERGENCE.md](TAIL-CONVERGENCE.md) shows that this adjustment disappears
from modeled state at 07B. An output consumer, timing effect, or revised decode
is needed before assigning it a sample-processing role.
[OUTPUT-CONTROL.md](OUTPUT-CONTROL.md) tests raw-bit output-enable predicates.
Forty-three different predicates fit the assumed example groups; their broad,
different predictions prevent identifying a strobe from these patterns alone.
[CONTROLLER-INTERFACE.md](CONTROLLER-INTERFACE.md) independently verifies the
8031 six-byte input/four-byte output protocol, normalization masks and P1
handshake ordering in 4,362 local ROM executions. Its physical link to the
microprogram remains unassigned.
[CONTROLLER-READ.md](CONTROLLER-READ.md) shows that the three observed callers
of the repeated 8004 read overwrite its returned byte. Any external side effect
of the bus cycle remains unknown; it is not an identified sample/status input.

## Datapath-derived lookup indices

[INDEX-SOURCES.md](INDEX-SOURCES.md) compares current Y, updated Q and retained
previous Y at the two ROM-backed branch sites. Tables may use `index_source`
to override the global dispatch source. `previous_y` requires an explicit
`dispatch.initial_y`; all datapath sources require integrated mode. No source
is promoted merely because it produces clean runs or higher coverage.

## Independent lookup-ROM dispatch evidence

[ROM-DISPATCH.md](ROM-DISPATCH.md) replaces several permissive target pools
with actual Am27S31 bytes, reaching 91.97% coverage while retaining explicit
site/bank/index assumptions. The ROM also contains an exact 65-sample quarter
sine table. Sparse targets may retain repeated entries with the explicit
`allow_duplicate_targets: true` flag; default duplicate rejection is unchanged.

## Structurally constrained target pools

[TARGET-POOLS.md](TARGET-POOLS.md) classifies disconnected entries by stack
requirements and tests permissive target pools at 26F, 21F and 2C4. Reset
coverage reaches 91.48%; actual dispatch encoding and physical I/O remain
unknown. Local entry probes classify roles but do not count toward coverage.

## Exceptional computed-call candidate

[EXCEPTIONAL-CALL.md](EXCEPTIONAL-CALL.md) tests 1A2 calling a local POP table,
reaching 80.51% coverage. A returning surrogate reaches 80.12%, so most of the
gain identifies a continuation problem rather than proving the target. Explicit
`dispatch.tables` entries override a call's direct hint; conditions and real
stack pushes remain unchanged.

## Low-address handler dispatch

[LOW-HANDLERS.md](LOW-HANDLERS.md) raises measured coverage to 75.42% under
explicit boundary-derived target hypotheses. Tables may specify a sparse
`targets` list instead of `base/count/stride`, with the same provenance
requirements. Static analysis and execution share target validation and order.

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

The [external-byte polling study](POLLING.md) releases the original previous-flag
reset loop at 1EC with a logged input sequence, preserving its branch policies.
The input source remains an explicit instruction-address-keyed stub.

The [poll caller study](POLL-CALLER.md) traces that comparison to an earlier
external byte: all 256 successor responses release the loop, while unchanged
responses do not, under the fixed original-register reset scenario.

The [paired Q-drain study](DOUBLE-DRAIN.md) explains the variable time before
that poll with two shift loops, matching all 256 saved reset timing cases.

A [contextual branch-bit search](CONTEXT-BRANCH.md) tests 1,024 alternatives.
One class of hypotheses adds 28A without losing coverage, but does not recover
the bit source or change the default runtime mapping.

The [joint branch study](JOINT-BRANCH.md) tests 7,489 pairs of clean contextual
alternatives. Its best coverage remains 1,000 words; new paths into 0FD come
with substantial coverage loss elsewhere.

The [raw-bit branch mux search](BRANCH-MUX.md) tests 8,192 gate/source choices.
None improves baseline coverage; its new path to 0FA loses 85 other words.

The [controller input decoder](CONTROLLER-DECODE.md) translates routine 0620
into explicit bit-field rules, checked against 10,144 unchanged-ROM executions.
Physical signal names remain unresolved.

The [controller event study](CONTROLLER-EVENT.md) follows a countdown-weighted
external interrupt into byte 6E and two outgoing buffer bits, checked against
30,436 ROM executions.

The [fourth output-byte study](CONTROLLER-OUTPUT.md) identifies its five-bit
state code and three flags, verified over all 65,536 state/flag assignments.

The [first two output-byte builders](CONTROLLER-OUTPUT-PAIR.md) preserve the
event-qualified bits and derive the remaining fields from state and selectors;
35,328 local ROM comparisons cover every instruction in that section.

The [third output-byte builder](CONTROLLER-OUTPUT32.md) combines state-code
bits with counter-controlled fields, verified in 103,424 local ROM executions.
All four byte builders now have local references; their full composition remains
to be checked.

[Continuous output construction](CONTROLLER-OUTPUT-BUILD.md) verifies all four
builders together and the immediate rotating-pattern/P1 and RAM30 override:
32,768 cases match uninterrupted ROM execution through 046A.

[Peripheral programming](CONTROLLER-PROGRAM.md) verifies the complete write
sequence of helper 1D05 at both USART control addresses: 7,168 cases, including
all mode bytes and all P2 address-page values in the stated fixture families.

[Output through transmission](CONTROLLER-OUTPUT-SEND.md) executes the actual
main-loop calls to 006E and 0899 continuously. All 32,768 cases match output,
mode programming, counters/patterns, and serial bytes; timer/interrupt state
and complete internal initialization semantics remain outside the comparison.

[Controller scrambling](CONTROLLER-SCRAMBLER.md) identifies and verifies the
23-bit scramble/descramble pair, with selectable delays (5,23) or (18,23).
An independent bit-serial reference matches 43,008 ROM cases and all 134
instructions in the local byte-processing routines.

[Biased Q shifting](BIASED-DRAIN.md) characterizes 296–29E under the selected
original-role/previous-flag policy. All 131,072 local D/Q cases match an
analytic return/repetition criterion; caller preconditions remain unresolved.

[Shift-loop caller](DRAIN-CALLER.md) follows wrapper 248 through two right
shifts and a left shift: 131,072 local cases match the composed termination
criterion, with separate bounded reset-path observations.

[Reset-driven shift callers](DRAIN-RESET.md) trace R7=FF and Q=D from reset
through seeded dispatch entry 1 at 109. Of 256 constant bytes per seed, only
zero lets the complete wrapper return; explicit changing-input diagnostics
release the loops without altering the mapping or sequencer state.

[Datapath dispatch at 109](DISPATCH109.md) compares scenario, current Y, Q,
and preceding Y across all input bytes. Under the fitted reset path, Y=D+1
selects all eight branch entries; the optional variant reaches 476 distinct
instructions across the sweep without establishing physical index wiring.

[Carry-controlled addition chain](CARRY-CHAIN.md) explains the 36C–36E loop:
139,264 local comparisons distinguish previous/current carry timing, and 32
reset-path replays explain its repetition under constant external input.

[Idempotent mask tests](MASK-LOOP.md) characterize 126–130 with 262,144 local
comparisons and 32 reset replays. These helpers select no external D operand,
so changing the read stub cannot release a failed containment test.

[Mask-loop mapping comparison](MASK-VARIANTS.md) finds that retained q2
interprets 12C as an external equality poll under the shared previous-flag
policy. All 65,536 mask/Q targets release on the diagnostic input change;
no default mapping or physical channel is selected.

[q2 reset callers](Q2-CALLER.md) establish zero-target masked polls after
carry-qualified early waits. Three external-input profiles across all byte
values give 768 clean runs; physical replies and nonzero targets remain unknown.

[q2 target provenance](Q2-TARGETS.md) sweeps all eight dispatch choices and
all input bytes. R10 can capture a nonzero value from R6, but none of the
2,048 tested paths carries that written value into a masked poll.

[q2 paired dispatch](Q2-DISPATCH.md) tests preceding Y at 38F: the prior
instruction supplies D−R14, while current Y and Q are zero in the reset
fixtures. This candidate releases 129 input cases from the arithmetic wrapper;
65 reach 084 and 64 reach a carry loop. Physical wiring remains unresolved.

[q2 accumulator gate](Q2-ACCUMULATOR.md) identifies a Q+=D update whose carry
gates transform calls, followed by an old-Q/R7 comparison. The 132,608 local
checks cover the arithmetic and threshold boundaries; all 256 tested reset
inputs start with Q=0 and bypass the calls.

[q2 transform wrapper](Q2-TRANSFORM-LOOP.md) checks 3C0 with real loop control.
It repeatedly transforms unchanged source words and returns when the second
result high byte is zero; other fixed-index cases repeat every eight instructions.
The study includes 263,344 local checks and 40 executions through the 133 gate.

[q2 source-overwriting loops](Q2-OVERWRITE.md) explains 3D5/3EA recurrence,
including second-pass returns and 16-instruction cycles. The complete 133
three-call path is checked with arithmetic flags over 400 local boundary cases.

[30B mapping comparison](MASKED-DRAIN.md) distinguishes a cleared-Q one-pass
helper under q1–q4 from a masked-Q drain under fitted_original. Across all
R0/Q pairs, final R5 differs in 56,788 cases; both interpretations clear R0/Q.

[Drain caller prefix](DRAIN-PREFIX.md) shows that a second call overwrites
the first R5 result before any selected consumer. Full-prefix state and timing
are checked across 139,264 cases; the existing 302 condition bypasses this
path, so these remain explicitly local caller fixtures.

[Register-difference scan](REGISTER-SCAN.md) explains the path taken at 302.
It preserves RAM/Q, exposes selected differences, and waits while R15>=R0
under the shared previous-carry policy. The rule is checked across all byte
pairs and 512 reset runs; fitted_original D=FF repeats the final loop.

[Unconditional-BRT gate search](UNCONDITIONAL-GATES.md) finds clean structural
alternatives reaching up to 1,011 used words, with 43 sequencer-replayed paths.
The gates use branch-address bits and have no recovered datapath condition
meaning; the default graph and its 22 unresolved words remain unchanged.

[Integrated BRT-gate study](GATE-RUNTIME.md) implements the optional raw-bit
gate with provenance validation and tests it in 8,192 matched reset runs.
Actual flags reach 2D9–2DB in both mappings and 0FA in one fitted-original
case. The default condition policy and unresolved-entry labels remain intact.

[Fixed-condition reachability](CONSTANT-CONDITIONS.md) restricts the graph to
the integrated scenario's constant inputs. The optional gated graph narrows
to 796 words, but all 12 previously added words retain sequencer-replayed
reset paths. Actual flag and dispatch dependencies remain unresolved.

[Expanded dispatch indices](DISPATCH-RANGE.md) reach 3BD–3BF in 16 q2 reset
cases using actual flags. An exhaustive local check explains this tail's
conditional difference and its choice between 287 and 3C0; RAM/Q are preserved.

[Q input and dispatch](Q-DISPATCH.md) reaches 2CF from reset by changing the
last Q-loading read to zero. Across 1,024 runs, Q-based dispatch removes that
entry combination, while a later Q clear explains the fixed 3BF exit.

[Tail exclusion under q2](TAIL-EXCLUSION.md) explains why 287–28A cannot execute
from zero reset under the optional gate, even with arbitrary byte reads and
declared dispatch entries. Complete predecessor checks and local register
invariants exclude both entries; default unresolved labels remain unchanged.

[Retained tail variants](TAIL-VARIANTS.md) reach 287–28A under q3 with the
same inputs excluded by q2. The decisive difference is Q−1 versus Q−R0−1,
not a nonzero Q in that witness. All 12 gate-added words now have reset
witnesses across explicitly different retained mappings and scenarios.

[Three-bit gate extension](THREE-BIT-GATES.md) exposes five more words in a
clean 1,016-word graph. Matched q2 reset runs enter the adjustment selector
when D+Q wraps R0 to zero; Q=FF selects the unadjusted tail. The gate remains
an optional structural hypothesis, with five words still disconnected.

[Identical-word gate limits](GATE-ALIASES.md) add a clean reset entry into 258
and a 1,017-word optional graph. The four remaining words cannot be admitted
by raw-only gate relaxation without free-flag stack-underflow paths; actual
flag correlations and alternative entry models remain open investigations.

[Actual flags at the 0FC alias class](ALIAS-RUNTIME.md) reach 0FD–0FF in 255
fitted_swapped reset cases. All 3,072 matched runs terminate cleanly, while
the conservative graph still exposes underflows at untested alias paths.
The continuation copies R2 to R0 and branches according to whether Q is zero.

[2DF entry and input boundary](LAST-ENTRY.md) supply clean q3/q4 FF reset
witnesses for the last disconnected word, while retaining 1,279 failing
extended-gate runs. The following masked-input test requires both bytes FF
when R0=0; the broader gate remains diagnostic rather than globally validated.

[Verified reset-witness catalog](RESET-WITNESSES.md) ties all 22 default graph
gaps to five complete runs. The listing generator replays their mappings,
scenarios, traces and I/O logs byte for byte, while retaining profile scopes,
conservative graph failures and default unresolved-entry labels.

[Independent captured bytes](PAIRED-CAPTURE.md) follow a low/high pair from
zero reset into paired arithmetic. Among 4,096 clean runs, 508 return despite
a nonzero low-byte result: the loop observes only the final high byte.
Physical output and the input protocol remain unresolved.

[Nested preparation and ROM leaves](NESTED-PREPARE.md) explain the q2
2BC wrapper and its seven nested targets. Across 262,144 local calls, the
prefix preserves Q while preparing shifted/summed registers; selected leaves
then preserve Q, replace it from D, or capture D+Q in R15. These are local
call fixtures, not new reset or physical-I/O coverage.

[Nested reset witnesses](NESTED-RESET.md) reach 2BC in five of 4,096
clean q2 runs with actual ALU flags and seeded dispatch. The real caller
context permits depth four and a balanced return through 2FF. The fixed
sweep visits 718 used words; the selected reset example is indexed separately.

[Save/load and byte-sum helper](AFFINE-TAIL.md) interprets 28E–295 under
q1/q2/q4: save old R0, optionally load Q, and form R0+2*R1+1 in R15.
393,216 local calls check both skip outcomes; five reset replays connect
the R0 copy to the following XNOR/skip decisions. R15 has no identified
physical consumer.

[Two indexed terminal stores](INDEXED-TAIL.md) identify the q2 08A–099
table as copies of R0 into each RAM register. The caller stores Q>>1 twice,
nine modeled instruction cycles apart. A preceding-Y address candidate
feeds back through R6 when the first store selects it. Four index candidates
remain compatible with clean termination but leave different RAM states.

[A diagnostic two-store input contract](REGISTER-CONTRACT.md) connects the
nested Q load to independently selected terminal register stores. It checks
65,536 continuations of an actual reset checkpoint and nine complete core
replays, retaining the R5 overwrite and the need to adjust the second index
when the first destination is R6. The physical protocol remains unknown.

[First-dispatch mapping comparison](SELECTOR-PREFIX.md) distinguishes the
current-Y/Q/previous-Y selectors across all six layouts. Independent reads
at 002 and 076 remove the constant-input parity restriction for q1/q3 and
reach all eight handlers through Q indexing. The q2/q4 current-Y limitation
remains explicit; no physical source or default layout is selected.

[Handler timing comparison](HANDLER-TIMING.md) follows all 256 input sums
through q1/q3 handlers under both flag timings and both early reply schedules.
Full-state recurrence distinguishes persistent loops from bounded traces;
changing timing trades successful handlers rather than resolving all waits.

[Handler-2 reply analysis](HANDLER-REPLY.md) connects the previous-flag poll
to terminal execution for all 32 input sums in q1/q3, while a decoded
R0/Q invariant excludes release of the current-flag loop by any later D
values or choices among its four candidate table entries.

[Independent paired components](PAIRED-COMPONENTS.md) follows a q3 input at
317 and the captured 16-bit word into two nonzero arithmetic components from
reset. The first high-byte result may be nonzero on return; only the final
high-byte result controls the loop. Matched q1 inputs expose the source-field
difference, and earlier-load controls verify the surviving input provenance.

[Selected sine-ROM operand](SINE-OPERAND.md) follows actual quarter-sine dump
bytes through q3 arithmetic to a surviving result, using an explicit ROM read
only at 317 and external replies elsewhere. Address setup and read-to-result
latency are logged in microinstructions; physical strobes and sample timing
remain unresolved.

[Raw-word ROM-read gates](ROM-GATE.md) replaces the single-PC sine read with
all activations of fitted control-word predicates. A two-bit gate preserves
the full quarter-sine path, but 136 three-bit alternatives also fit the assumed
labels and pass the tested boundaries while predicting different bus reads.

[ROM gates across handlers](ROM-GATE-HANDLERS.md) separates four execution
classes among the 137 fitted predicates. The two-bit gate creates a three-cycle
ROM/carry wait in handler 5; a zero external reply releases it. Other gates
change handler 2’s comparison value, showing why termination alone is not
evidence of the physical read-selection signal.

[ROM/carry reply recurrence](ROM-CARRY-REPLIES.md) derives the complete
256-state feedback transition for each reply byte. All 65,536 local transitions
match the ALU model; actual reset runs distinguish 215 returning replies from
41 persistent cycles, including a 45-instruction cycle.

[Entry-policy audit](ENTRY-POLICY-AUDIT.md) adds causal explanations for every
default gap: exact witness paths identify the forced jumps that must permit
fallthrough. All 4,096 subsets of twelve witnessed relaxations are checked;
32 reach every used word, and all retain a possible 2FF stack underflow.

[Return-wrapper stack contract](TAIL-STACK-CONTRACT.md) explains why 2FF
requires an incoming caller frame. The underflow survives fixed constant
selectors, and q3’s difference guard supplies a concrete condition for selecting
the tail. Clean and failed full-reset examples are both replayed.

[Masked nested dispatch](MASKED-NESTED-DISPATCH.md) drives both nested call
indices from nonzero q3 input masks. Real reset reads select 2BC and its inner
leaf, preserve or replace Q as predicted, and return through the existing
four-entry stack without injected state.

[Direct q3 register destinations](Q3-REGISTER-CONTRACT.md) connects the nonzero
masked nested reset path to two half-Q stores. All 65,536 payload/destination
combinations match the full-register contract; first R6 no longer changes the
second address, while first R5 is still overwritten by the second helper.

[Handler 6 masked capture](HANDLER6.md) explains 09E–0CD and exit 0DE under
q3: a captured byte is masked by the input code, conditionally incremented
using logical carry, and halved into surviving registers. Two Q drains account
for input-dependent timing; the FF mask wraps to zero before halving.

[Handler 1 wrapped byte sum](HANDLER1.md) follows independent input bytes
into R14 through an eight-bit sum and right shift under q3. A complete final
register formula and instruction-count formula explain the tested reset paths;
all 65,536 local byte pairs distinguish wrapping from ordinary averaging.

[Handler 4 input selection](HANDLER4.md) connects a sum-carry exit, a byte
comparison and a logical-XOR skip to retained Q and terminal register stores.
Exhaustive A/B continuations distinguish captured R7=00/FF, with complete
reset replays checking all intermediate and final state.

[Explicit DAC output hypotheses](DAC-OUTPUT.md) replay the live sine-path
bytes through a datasheet-based DAC0830 digital buffer model. Candidate byte
routes and transfer policies produce distinct retained codes and update times;
all connections remain labelled hypotheses, and core traces are unchanged.

[Reset preparation helpers](RESET-HELPERS.md) explain q3 06F–077 and
112–116, including the carry-selected half/difference boundaries, Q input
accumulation and overwritten register copies. Local calls and an unchanged
reset witness verify the preconditions used by later handlers.

[Six short-helper contracts](SHORT-HELPERS.md) distinguish retained register
effects from transient Y sequences under q3. The 238/240 pair retains identical
RAM/Q but exposes carry-adjustment results in a different order; no external
consumer is assigned to those values.

[Conditional helper contracts](BRANCH-HELPERS.md) explain q3 270, 335 and
357 across explicit branch policies. They separate an overflow-selected register
copy, optional captures and Q complement, and three transient return sums
with identical retained state. Local calls do not imply reset reachability.

[The complete carry helper](CARRY-HELPER.md) connects q3 366 preparation,
the carry-controlled wait and the final external-byte/Q mask into one checked
call. Constant-input recurrence and a real zero-reply reset call are verified
separately from the existing changing-ROM feedback recurrence.

[The paired self-arithmetic wait](PAIR-WAIT.md) explains q3 370 and its
four-entry table, including high-byte-only return, exact period-12 recurrence,
and the distinction between preceding-Y input selection and current-Y zero.

[Input preparation and comparison tail](INPUT-TAIL.md) explains q3 2EC
through its real nested return. Three paths differ in intermediate Q and timing,
but the declared 224 leaf reloads Q and gives a common final-state contract.
This completes the direct-call naming queue; broader program reading remains.

[Timed external line and handler-3 continuation](EXTERNAL-LINE.md) introduces
a provenance-labelled cycle schedule without PC branch overrides. It preserves
boot while reaching the double-preparation and paired-wait path from reset,
and explains why these contexts still exclude 1EF. Recurrence checks account
for future scheduled input changes.

[A completion-qualified controller-to-DAC bridge](FRAME-DAC-BRIDGE.md) executes
the actual controller builder/transmitter, gates startup on full frame completion
and latch, routes bytes into a zero-reset microcode run, and drives recurring DAC
transfers. The connection and time ratio are explicit hypotheses; the held codes
are constant and no autonomous phase advance or return protocol is inferred.

[Handler 7 carry-selected transforms](HANDLER7.md) connects independent input
bytes and captured R7 to zero, one or three transform calls from actual reset.
The resulting R1–R3 differences survive terminal entry, with checked cycle
counts and zero-source termination under the declared table entry.

[Handler 5 continuation composition](HANDLER5-BRANCHES.md) connects all three
34C cases to actual reset and terminal R2 stores. It distinguishes Q=0/c/FF,
which input survives in R4, and the retained R3=3 caused by entry at 07B.

[Handler 0's fixed-register waits](HANDLER0.md) distinguish q3's zero/Q
source from the fitted-original mask test. Current timing permits the full
reset arithmetic sequence; intermediate Q inputs are overwritten before
terminal storage, while the captured R4 sum survives.

[Handler 2 preparation and continuation](HANDLER2-BODY.md) connects the
carry-selected FE/FF comparison byte, wrapped-sum drain timing, paired detour,
external reply and terminal payload stores. The reply depends on a real
upstream input; 02 is specific to the earlier default-input context.

[Handler 2's alternative timed routes](HANDLER2-ROUTES.md) reach 1C3 and
1DA through scheduled external conditions. The direct body and 2D0 detour
retain the same final state but differ in carry-biased Q loading and drain
timing, including the FF wrap boundary.

[Early dispatch and the fixed-register wait](EARLY-WAIT.md) compares all
eight alternative boot entries, proves the 05D loop predicates, and follows
the Q-clearing entry through a complete terminal register contract. The D read
inside the repeating loop cannot release it under this decode.

[Early entry 013's call-fed carry wait](EARLY-ENTRY13.md) explains the real
initial BSR/BLT frame, the external reply threshold at 01D, and why 01E's own
input does not select the branch. Release leads to a separately controlled
Q reload and the already checked 05D wait or terminal tail.

[Early entry 022's carry-selected loop pop](EARLY-ENTRY22.md) explains the
input threshold that either executes BLT or skips it with its PLP frame still
present. Local fixtures also verify the Q-zero shift branch excluded by this
reset entry. Both reset paths join the same fixed-register wait.

[Early entry 032's nested choices](EARLY-ENTRY32.md) connects both declared
indices to retained R3, the 03F skip and the FF carry boundary through 045.
Checked formulas distinguish terminal entry from the shared fixed-register
wait; bypassed 043/044 remain outside the annotation.

[Handler 3's alternate component and drains](HANDLER3-DRAINS.md) reaches
1EF using an explicit two-selector external-line hypothesis, with unchanged
baseline prefixes and negative entry controls. The constructed R5 component
survives into paired Y outputs before terminal helpers overwrite it.

[Handler 6's late captured-value exits](HANDLER6-LATE.md) reaches 0CE and
0DF through timed selector-1 inputs. A captured value and masked input select
two terminal entries, with checked retained state and an additional complement
boundary in the terminal skip.

[Handler 6's early complement diversion](HANDLER6-EARLY.md) reaches 0E0
from either earlier selector-1 branch. Q=FF reverses the later capture's bias
and makes the 0CF input addition conditional on an FF capture at 0C6; complete
retained-state and timing formulas distinguish this from the late-only entry.

[Handler-4 bank continuations](HANDLER4-BANK.md) follow 200/204/217 through
nested payload loading, capture replacement or preservation, and terminal
indexed stores, with complete register and timing contracts from reset.

[Handler-4 alternatives](HANDLER4-ALTERNATIVES.md) explain the timed 265
preparation, the two input additions through 230/0ED and the direct 280 path,
including complete terminal state, store overlaps and negative timing controls.

[Handler-1 branch continuations](HANDLER1-BRANCHES.md) explain how an earlier
input's parity controls the 17F skip, while scheduled external-line changes
select equal-result paths with different microinstruction counts.

[Handler-2 alternate preparation](HANDLER2-ALTERNATE.md) explains 1E0–1E4
under an explicit external-source hypothesis and all four 1E5–1E8 return
leaves under preceding-Y dispatch, preserving negative entry controls.

[Startup contract](STARTUP-CONTRACT.md) explains the shared entry sequence,
its two independently controlled capture waits, complete state at all eight
handler entries and deterministic held-wait recurrence.

[Outer input leaves](INPUT-LEAVES.md) explain the nested temporary-input call
at 221 and the comparison-qualified return through 2B9–2BB, with all selecting
ROM-table indices and explicit caller-state differences.

[Final branch blocks](FINAL-BLOCKS.md) close the remaining word-level annotation
gaps with an early clear/capture diversion and a current-flag complement exit.
All used words now have scoped interpretations; program-level synthesis and
final requirement review remain outstanding.
