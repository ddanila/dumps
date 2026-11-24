# Assumption-driven DSC2847 microcode experiment

The DSC 2847 microcode, executed under explicit, labelled assumptions about
its unknown wiring. This is the work of [PLAN.md](../PLAN.md), which is
complete. The next phase, [PLAN-2.md](../PLAN-2.md), constrains these
assumptions against the V.26 ter evidence.

**Read every study under [ASSUMPTIONS.md](ASSUMPTIONS.md).** That page has the
shared configuration, how to reproduce runs, and what the results can and
cannot show. Results are runs under declared assumptions, not recovered Nokia
wiring.

Run outputs are under [`results/`](results/). Raw per-run traces are not
committed; each study script regenerates them.

## Start here

Overview, the annotated listing and acceptance.

| Study | Subject |
| --- | --- |
| [PROGRAM-OVERVIEW](PROGRAM-OVERVIEW.md) | What the microprogram does under the tested assumptions |
| [PROGRAM-READING](PROGRAM-READING.md) | Read the program by address |
| [FINAL-REVIEW](FINAL-REVIEW.md) | Final review against PLAN.md |
| [PLAN-AUDIT](PLAN-AUDIT.md) | Plan acceptance audit |
## Startup and early entries

Reset path, register preparation, input waits and early dispatch.

| Study | Subject |
| --- | --- |
| [STARTUP-CONTRACT](STARTUP-CONTRACT.md) | Startup: preparation, two byte waits and handler selection |
| [RESET-HELPERS](RESET-HELPERS.md) | q3 reset preparation helpers 06F and 112 |
| [EARLY-WAIT](EARLY-WAIT.md) | Early dispatch and the fixed-register wait at 05D |
| [EARLY-ENTRY13](EARLY-ENTRY13.md) | Early entry 013: an input-carry wait followed by a fixed-register wait |
| [EARLY-ENTRY22](EARLY-ENTRY22.md) | Early entry 022: shift selection and a skipped loop pop |
| [EARLY-ENTRY32](EARLY-ENTRY32.md) | Early entry 032: nested choices and comparison-input selection |
| [POLLING](POLLING.md) | External-byte poll at 1EC |
| [POLL-CALLER](POLL-CALLER.md) | Caller establishes a successor-byte poll |
| [FINAL-BLOCKS](FINAL-BLOCKS.md) | Final branch blocks: early clear/capture and current-flag exit |
## The eight handlers

Per-handler contracts under the q3 profile unless stated.

| Study | Subject |
| --- | --- |
| [HANDLER0](HANDLER0.md) | Handler 0: fixed-register waits and transient arithmetic |
| [HANDLER1](HANDLER1.md) | Handler 1: wrapped byte sum and shift-loop timing |
| [HANDLER1-BRANCHES](HANDLER1-BRANCHES.md) | Handler 1: input parity and timed terminal continuations |
| [HANDLER2-BODY](HANDLER2-BODY.md) | Handler 2: comparison preparation, Q drains and payload storage |
| [HANDLER2-ROUTES](HANDLER2-ROUTES.md) | Handler 2: timed continuation choices and carry-biased drains |
| [HANDLER2-ALTERNATE](HANDLER2-ALTERNATE.md) | Handler 2: alternate carry preparation and computed return leaves |
| [HANDLER-REPLY](HANDLER-REPLY.md) | Handler 2: external reply versus an invariant loop |
| [HANDLER3-DRAINS](HANDLER3-DRAINS.md) | Handler 3: alternate drains and a transient paired component |
| [EXTERNAL-LINE](EXTERNAL-LINE.md) | Timed external input and the handler-3 continuation |
| [HANDLER4](HANDLER4.md) | Handler 4: sum-carry and comparison-selected inputs |
| [HANDLER4-BANK](HANDLER4-BANK.md) | Handler 4: bank-200 input replacement and capture preservation |
| [HANDLER4-ALTERNATIVES](HANDLER4-ALTERNATIVES.md) | Handler 4: alternate preparation and two additive continuations |
| [HANDLER5-BRANCHES](HANDLER5-BRANCHES.md) | Three q3 handler-5 continuations |
| [HANDLER6](HANDLER6.md) | Handler 6: masked capture and two Q drains |
| [HANDLER6-EARLY](HANDLER6-EARLY.md) | Handler 6: early complement diversion and conditional input addition |
| [HANDLER6-LATE](HANDLER6-LATE.md) | Handler 6: late capture, masked input and two terminal entries |
| [HANDLER7](HANDLER7.md) | Handler 7: input carry selects transform calls |
## Shared helpers and arithmetic

Short helpers, paired arithmetic, Q drains and input tails.

| Study | Subject |
| --- | --- |
| [SHORT-HELPERS](SHORT-HELPERS.md) | Six q3 short-helper contracts |
| [BRANCH-HELPERS](BRANCH-HELPERS.md) | Three q3 conditional helpers |
| [CARRY-HELPER](CARRY-HELPER.md) | The complete q3 carry-gated input helper at 366 |
| [CARRY-CHAIN](CARRY-CHAIN.md) | Carry-controlled three-add loop at 36C |
| [PAIR-WAIT](PAIR-WAIT.md) | The q3 paired self-arithmetic wait at 370 |
| [PAIRED-CAPTURE](PAIRED-CAPTURE.md) | Independent captured bytes reach the paired-arithmetic loop |
| [PAIRED-COMPONENTS](PAIRED-COMPONENTS.md) | Two nonzero components reach paired arithmetic from reset |
| [AFFINE-TAIL](AFFINE-TAIL.md) | Saving R0, optionally loading Q, and forming a byte sum |
| [BIASED-DRAIN](BIASED-DRAIN.md) | Q shifting with input-dependent termination at 296 |
| [DOUBLE-DRAIN](DOUBLE-DRAIN.md) | Two Q drains explain the variable time before polling |
| [DRAIN-CALLER](DRAIN-CALLER.md) | The caller combines three input-dependent shift loops |
| [DRAIN-PREFIX](DRAIN-PREFIX.md) | The caller overwrites the first drain result before consuming it |
| [DRAIN-RESET](DRAIN-RESET.md) | Reset-driven paths establish the shift wrapper's sensitive inputs |
| [MASK-LOOP](MASK-LOOP.md) | Idempotent mask tests at 127 and 12C |
| [INPUT-LEAVES](INPUT-LEAVES.md) | Outer input leaves: replacement and comparison-qualified return |
| [INPUT-TAIL](INPUT-TAIL.md) | The q3 input-preparation and comparison tail at 2EC |
| [REGISTER-SCAN](REGISTER-SCAN.md) | The 302 branch reaches a register-difference scan |
## Nested calls and operand flow

Computed calls, transform wrappers and where operands come from.

| Study | Subject |
| --- | --- |
| [NESTED-PREPARE](NESTED-PREPARE.md) | Shifted-Q preparation and nested ROM dispatch |
| [NESTED-RESET](NESTED-RESET.md) | The nested ROM wrapper executes from zero reset |
| [MASKED-NESTED-DISPATCH](MASKED-NESTED-DISPATCH.md) | An input mask selects both nested ROM calls from reset |
| [ROM-TAIL](ROM-TAIL.md) | The D0/D1 ROM tail and the nested computed-call wrapper |
| [OPERAND-PATHS](OPERAND-PATHS.md) | Control-flow separation of source writers and transforms |
| [OPERAND-PROVENANCE](OPERAND-PROVENANCE.md) | Where the paired-arithmetic operands come from |
| [FIRST-USE](FIRST-USE.md) | Downstream use of surviving preparation data |
| [CALLER-CHAIN](CALLER-CHAIN.md) | Following preparation bytes through the caller chain |
| [SINGLE-CALLER](SINGLE-CALLER.md) | Preparation data survives the alternate 18B caller |
| [LOCAL-CASES](LOCAL-CASES.md) | Additional cases after local branch entries |
## q2 profile

Behaviour under the alternative q2 source mapping.

| Study | Subject |
| --- | --- |
| [Q2-ACCUMULATOR](Q2-ACCUMULATOR.md) | q2 handler 133 gates transforms on accumulator carry |
| [Q2-CALLER](Q2-CALLER.md) | q2 reset reaches zero-target polls through explicit external replies |
| [Q2-DISPATCH](Q2-DISPATCH.md) | Preceding Y selects nontrivial q2 paired-arithmetic paths |
| [Q2-OVERWRITE](Q2-OVERWRITE.md) | q2 transform wrappers can alternate their own source values |
| [Q2-TARGETS](Q2-TARGETS.md) | q2 can capture a nonzero R10, but the tested polls still use reset zero |
| [Q2-TRANSFORM-LOOP](Q2-TRANSFORM-LOOP.md) | q2's 3C0 wrapper repeats a fixed transform until its high-byte test passes |
## Terminal tail and stack

The common tail, the 084 self-loop and stack contracts.

| Study | Subject |
| --- | --- |
| [TERMINAL-TAIL](TERMINAL-TAIL.md) | The common terminal tail and the 084 self-loop |
| [TAIL-CONVERGENCE](TAIL-CONVERGENCE.md) | The adjustment is transient in the current model |
| [TAIL-EXCLUSION](TAIL-EXCLUSION.md) | Why the remaining gated tail cannot execute under q2 |
| [TAIL-STACK-CONTRACT](TAIL-STACK-CONTRACT.md) | 2FD–2FF requires an incoming return frame |
| [TAIL-VARIANTS](TAIL-VARIANTS.md) | A retained alternative reaches the excluded tail |
| [INDEXED-TAIL](INDEXED-TAIL.md) | Two indexed register stores in the terminal tail |
## Sequencer fields, dispatch and reachability

Branch-address bits, dispatch sources, gates and the default graph's gaps.

| Study | Subject |
| --- | --- |
| [BRANCH-BITS](BRANCH-BITS.md) | Global branch-address bit alternatives |
| [BRANCH-MUX](BRANCH-MUX.md) | Raw-bit-controlled branch address mux search |
| [CONTEXT-BRANCH](CONTEXT-BRANCH.md) | Command/selector-scoped branch address alternatives |
| [JOINT-BRANCH](JOINT-BRANCH.md) | Pairing clean contextual branch alternatives |
| [CONSTANT-CONDITIONS](CONSTANT-CONDITIONS.md) | Reachability with fixed condition inputs |
| [TARGET-POOLS](TARGET-POOLS.md) | Structurally constrained target pools: 91.48% reset coverage |
| [ROM-DISPATCH](ROM-DISPATCH.md) | Am27S31 data constrains dispatch targets |
| [DISPATCH-RANGE](DISPATCH-RANGE.md) | Expanded dispatch indices and the conditional difference tail |
| [DISPATCH109](DISPATCH109.md) | Input-derived dispatch candidate at 109 |
| [Q-DISPATCH](Q-DISPATCH.md) | Q input, computed dispatch and the zero tail |
| [INDEX-SOURCES](INDEX-SOURCES.md) | Datapath-derived indices at the ROM-backed branches |
| [ENTRY-POLICY-AUDIT](ENTRY-POLICY-AUDIT.md) | Causal explanations for the default graph's 22 gaps |
| [RESET-WITNESSES](RESET-WITNESSES.md) | Verified reset witnesses for the default graph gaps |
| [FRAGMENTS](FRAGMENTS.md) | Disconnected entry families and a conditional one-unit adjustment |
| [UNCONDITIONAL-GATES](UNCONDITIONAL-GATES.md) | Conditional BRT alternatives expose clean paths to disconnected fragments |
| [THREE-BIT-GATES](THREE-BIT-GATES.md) | A three-bit gate extension and reset entry into the adjustment selector |
| [GATE-ALIASES](GATE-ALIASES.md) | Identical-word limits and a clean entry into 258 |
| [GATE-RUNTIME](GATE-RUNTIME.md) | Testing the BRT gate with integrated datapath flags |
| [SELECTOR-PREFIX](SELECTOR-PREFIX.md) | First-dispatch selectors depend on both mapping and input schedule |
| [SELECTOR-COMPLETION](SELECTOR-COMPLETION.md) | Reset reaches preparation when unconstrained selector 5 is asserted |
| [ALIAS-RUNTIME](ALIAS-RUNTIME.md) | Actual flags admit the 0FD–0FF continuation |
| [LAST-ENTRY](LAST-ENTRY.md) | 2DF: a successful reset entry and an input-dependent failure boundary |
## Condition flags and timing

Which flags feed the sequencer TEST input, and when.

| Study | Subject |
| --- | --- |
| [CONDITION-TIMING](CONDITION-TIMING.md) | Select-zero nonzero condition experiment |
| [CONDITION-FIT](CONDITION-FIT.md) | Consistent flag policies for the two numerical-use witnesses |
| [CONDITION-EXTENSION](CONDITION-EXTENSION.md) | Extending the fitted condition policies |
| [DEFINED-CONDITIONS](DEFINED-CONDITIONS.md) | Condition fits with defined logical flags |
| [LOGIC-FLAGS](LOGIC-FLAGS.md) | Defined logical flags remove a carry-feedback assumption |
| [HANDLER-TIMING](HANDLER-TIMING.md) | Input-selected handlers and flag timing |
## Datapath field recovery

Register, source and destination field candidates.

| Study | Subject |
| --- | --- |
| [REGISTER-FIELDS](REGISTER-FIELDS.md) | Second register field and a datapath limitation |
| [Q-INDEPENDENT](Q-INDEPENDENT.md) | Separated source fields and a shift-until-zero routine |
| [PAIRED-ARITHMETIC](PAIRED-ARITHMETIC.md) | Paired arithmetic hypothesis |
| [CALLER-STATES](CALLER-STATES.md) | Caller states challenge the simple rotation interpretation |
| [PREPARATION-DECODE](PREPARATION-DECODE.md) | Testing the preparation routine against the arithmetic decode |
| [MASK-VARIANTS](MASK-VARIANTS.md) | Retained q2 mapping interprets the mask loop as an external poll |
| [MASKED-DRAIN](MASKED-DRAIN.md) | The 30B helper distinguishes retained source mappings |
| [REGISTER-CONTRACT](REGISTER-CONTRACT.md) | A diagnostic input contract for two register stores |
| [Q3-REGISTER-CONTRACT](Q3-REGISTER-CONTRACT.md) | Direct destination bytes under q3 |
## Lookup ROM, DAC and controller I/O

Real Am27S31 bytes in arithmetic, read gates, DAC writes and the controller bridge.

| Study | Subject |
| --- | --- |
| [ALU-FEEDBACK](ALU-FEEDBACK.md) | Lookup-ROM feedback into the ALU |
| [SINE-OPERAND](SINE-OPERAND.md) | Actual sine-ROM bytes reach arithmetic under a selected-read hypothesis |
| [ROM-GATE](ROM-GATE.md) | A raw-word ROM-read gate preserves the sine path, but remains ambiguous |
| [ROM-GATE-HANDLERS](ROM-GATE-HANDLERS.md) | ROM-gate predictions across eight handlers |
| [ROM-CARRY-REPLIES](ROM-CARRY-REPLIES.md) | The ROM/carry wait has a finite feedback recurrence |
| [DAC-OUTPUT](DAC-OUTPUT.md) | Explicit DAC0830 output hypotheses |
| [OUTPUT-CONTROL](OUTPUT-CONTROL.md) | Output-control patterns remain ambiguous |
| [FRAME-DAC-BRIDGE](FRAME-DAC-BRIDGE.md) | A completion-qualified controller-to-DAC diagnostic transaction |
## Early experiments

Superseded by the studies above; kept for reproducibility.

| Study | Subject |
| --- | --- |
| [JOURNAL](history/JOURNAL.md) | Experiment journal (historical) |
| [RESULTS](RESULTS.md) | Measured results |
| [BRANCH-TABLES](history/BRANCH-TABLES.md) | Local branch-table experiment |
| [LOW-HANDLERS](history/LOW-HANDLERS.md) | Low-address handler dispatch: 75.42% measured coverage |
| [EXCEPTIONAL-CALL](history/EXCEPTIONAL-CALL.md) | Exceptional call at 1A2: local return-table hypothesis |
