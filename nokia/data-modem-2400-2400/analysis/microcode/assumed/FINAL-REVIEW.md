# Final review against PLAN.md

*Runs under the [shared assumptions](ASSUMPTIONS.md).*

The implementation satisfies steps 1–5 of the original plan under its explicit
assumption policy. Step 6 is optional. This is a review of the executable
implementation and its evidence, not certification of Nokia wiring or a claim
to have identified the modem's original signal-processing algorithm.

The original plan remains unchanged. In particular, its allowance for a short
list of layouts, scenario-supplied dispatch, explained reachability exceptions
and unknown hardware is retained. Neither hardware measurements nor a single
physical decode have been added as completion requirements. Conversely, legal
instruction decoding, annotation counts and error-free idle loops alone were
not treated as sufficient evidence.

## Working rules and preservation

`common.py` decodes fields from mapping files. `execute.py` validates scenario
provenance, dispatch tables and condition sources. It passes the scenario's
carry and RAM/Q shift inputs into the datapath, selects current or previous
flags as configured, and records unknown-flag substitutions. External operands
are supplied through constant, table, ROM or declared sequence policies. Trace
records include ALU operands/results, register changes, branch decisions and
stack state; configured writes include address, value and provenance.

No scenario repairs a stack. The executor rejects `stack_fallback`, preserves
the component's circular-stack semantics, records depth violations and marks
such runs unclean. Regression tests exercise underflow and overflow, failed
and truncated witnesses, timing alternatives and input-dependent recurrence.

The consolidated verifier checks acquisition hashes for all 22 photographs
and six ROM binaries. It re-executes the analyses and compares generated
artifacts, rather than trusting the presence of saved output files. Historical
experiments retain their original failures and limitations.

## Step 1: analysis and address accounting

Inspected `analyze.py` implements the command histogram, must-target set,
2,208 address windows, greedy bit refinement, B0/B9 alternatives, linear
subroutine walks and condition table. Its generated listing includes raw words,
decoded fields and remaining bits. The graph labels calls, loops, returns and
configured dispatch edges. The consolidated run reproduces all 11 analysis
artifacts exactly.

The 01E outlier is an actual loop-body entry: BSR at 01C pushes 01D, and BLT
at 01E consumes that frame. Both test outcomes are exercised in
`test_real_statistics_and_loop_entry`; address-search scores reproduce at 33.

The later graph accounts for 999 used words. For each of its remaining 22,
`reset_witness_catalog.py` replays a complete reset execution and records the
specific suppressed fallthroughs required to reach it. The listing preserves
default-unresolved labels and the alternate policy evidence separately. The
three all-FF unused words remain excluded. The possible 2FF underflow under
broader relaxed policies is documented, not erased to obtain full coverage.
This meets the plan's reachable-or-explained-exception criterion.

## Step 2: sequencer execution

The executor drives the existing `X8X02.step` with the decoded command, target
and test. Constant, per-select and seeded random modes are implemented and
tested, including polarity and unconditional-transfer behavior. Computed calls
push real return addresses; branch tables do not push. Per-site table bases,
strides or explicit target lists carry hypothesis provenance and bounds checks.

The current 128-seed sweep reaches 941 of 1,021 used words with clean stack
results. Each digest and stack summary reproduces its reference. The separate
million-instruction sequencer run and full replay are clean, with depth at
most four. The original 28.80% suite remains a failed coverage result. These
are separate experiments, and the newer sweep meets the “most of the store”
criterion without relabelling the historical suite.

## Step 3: datapath alternatives

The initial ranking scores register-table diversity, common destinations,
loop setup and shifts, preserving tied A/B alternatives. It explicitly tests
the reversed chip-10 immediate hypothesis in non-branch contexts. Later
register-field and Q-source studies feed failed interpretations back into the
search: nonzero Q invalidated an earlier table interpretation, and the
separated source-bit search retained four named alternatives instead.

The consolidated listing includes those four and the two fitted A/B-role
variants. Each decodes all 1,024 words. Plausibility is supported beyond
legality by nonzero arithmetic fixtures, all-byte shift-loop termination,
input-dependent reset contracts and explicit counterexamples for overlapping
source registers. The quarter-turn identities used as search constraints are
not presented as independent confirmation. The ROM-operand and DAC buffer
experiments add real dump bytes and output-width/timing constraints without
pretending to identify a unique physical connection.

This meets the plan's named-shortlist criterion. It does not prove that every
variant is equally plausible, or that the board uses any one in particular.

## Step 4: integrated execution

`Am2901` models the two slices as an eight-bit datapath with ordinary carry
and shift cascading; unknown external shift inputs remain scenario values.
The executor supports zero, sign, carry, overflow and external conditions,
with switchable polarity and current/previous timing. Q, current Y and previous
Y can supply dispatch indices, including per-site overrides. The masked
nested-reset studies demonstrate data-derived indices with real caller frames.

Two primary integrated runs execute one million instructions each, followed by
exact full-summary/digest replays. The q2 run reaches a real depth-four nested
call and terminal state. The q3 ROM/carry run continues changing state, with
333,309 ROM operand reads and 999,941 register changes. Thus the sustained-run
evidence includes active arithmetic and address feedback, not only terminal
spinning. Bounded traces, full-run counters, source hashes and saved scenarios
make the results inspectable and repeatable. Tests reject unclean runs, short
execution, excess depth, replay mismatch and inadequate coverage.

## Step 5: program reading and other boards

The [overview](PROGRAM-OVERVIEW.md) joins startup, eight handler contracts,
helper families, output behavior and terminal waits. The
[annotated listing](PROGRAM-READING.md) covers all 1,021 used words and all 37
cataloged direct-call entries, retaining profile scopes and evidence links.
The interpretations distinguish retained state from transient Y values,
external wait control from captured data, local fixtures from reset runs, and
arithmetic results from their unknown physical purpose.

Evidence includes independent input variation, boundary and wraparound cases,
negative controls for branch timing/source changes, complete final-register
predictions and deterministic recurrence checks. The final two studies close
043/044 and 1DC–1DE with actual caller contexts, rather than merely assigning
names to the last unlabeled instructions. The 137-test regression suite
exercises these contracts as well as the model, dispatch and evidence tools.

The controller bridge executes the unchanged 8031 builder/transmitter and
requires the fourth transmission completion before the latch. Six complete
transactions and four incomplete controls are replayed exactly. Unchanged
wire bytes feed declared microcode read sites, actual ROM bytes participate in
arithmetic, and a DAC0830 digital-buffer model records recurring transfers.
The checked relative timing spans frame completion, startup, ROM address/read
and output transfer. The arbitrary clock ratio is explicit; no physical sample
frequency is inferred. The outputs hold constant codes, so the study does not
claim an autonomous waveform or bidirectional controller protocol.

These establish the required relation to sine lookups, DAC writes, timing and
controller exchange within the plan's allowed assumptions. Naming an actual
filter or demodulator without supporting evidence would go beyond the result.
The revised source mappings, condition timing, ROM gates and caller studies
demonstrate the required feedback from interpretation into steps 3–4.

## Step 6 and acceptance

Continuity checks remain optional ways to distinguish dispatch, condition and
instruction wiring. They are not outstanding implementation work under this
plan. Physical fidelity, unknown output consumers and the original modem's
algorithm remain documented research questions.

The current `PLAN-AUDIT.md` table maps every required item to evidence.
`plan_validation.py` records this reviewed acceptance separately from its
runtime execution gate and fingerprints this review and the program overview.
The full-plan flag is a recorded review decision guarded by current execution
and annotation checks; it is not an automated proof that prose annotations
are correct. Acceptance requires the reviewed evidence above, the successful
regression result and successful consolidated replay together.
