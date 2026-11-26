# DSC2847 microcode emulation plan

> **Status:** G1 complete ([final review](assumed/FINAL-REVIEW.md)); **G2 active**
> in [PLAN-2.md](PLAN-2.md#goal-g2). G2 remains active when a
> photographed connection is ambiguous: model the plausible connections as
> labelled assumptions, run them, and use the results to choose the next test.
> Missing continuity data or an untraced board connection is not a reason to
> mark G2 blocked; unresolved acceptance checks stay open while experiments
> continue. Treat each failed candidate as a result about its stated wiring,
> timing and inputs, then test another photo-compatible route or independent
> program/signal constraint.

**Current blocker approach:** Missing DAC, ADC, latch, clock, DSC-to-USART and
analog-line connections are *open wiring hypotheses*, not a stop condition.
Treat missing physical evidence as a limit on what a run can prove, not on
whether the next run can start. Keep the relevant acceptance check open and
continue with an explicit candidate connection or independent PROM, controller
or signal constraint. If several candidates remain indistinguishable, report
that ambiguity and pursue a different discriminating test; do not wait for a
photograph or continuity measurement to resolve it.
When a photo shows only part of a net, choose the simplest pin-compatible
continuation as the working assumption, label every unseen segment, inversion
and clock/latch phase, and run the real PROMs with relevant controller traffic.
Compare a few alternatives that could change the result and retain a control
with the same input and startup state. A failure rejects only the stated
fixture; select another photo-compatible route or independent program/signal
constraint. A success remains conditional until the physical route is
independently constrained. Report the working assumption, its distinguishing
result and the next executable test; do not request continuity measurements
or new photographs as a prerequisite. For C2, test the candidate Y7-to-latch-
to-DAC08 MSB and analog-output route identified by the [MSB-only replay](g2/JOINT-MASK04-DAC-MSB-DATA.md).
For C3, test a photo-compatible multi-visit consumer of `3F8`/`3ED` output,
including intermediate carrier phases, then its RxD/RxC and external SYNDET
route; the [two-visit selector](g2/RECEIVER-MASK04-PREAMBLE-TWO-VISIT-SELECTOR.md)
is a conditional grid baseline. Keep G2 active while such experiments are
possible. Unmet C2, C3 and C4 checks stay open; a plausible waveform or
decoded bitstream does not by itself verify a physical connection.
The [frozen frequency-offset replay](g2/RECEIVER-MASK04-FREQUENCY-OFFSET.md)
now tests −7, 0 and +7 Hz on six real-PROM streams. It makes no wrong known
decisions, but leaves three data dibits unknown at +7 Hz across the two
phases. The [adjacent-visit replay](g2/RECEIVER-MASK04-OFFSET-VISIT-PHASE.md)
captures both sides of the ADC sample boundaries with the same frozen
readout. Visit pair 46/93 recovers all 64 data dibits at +7 Hz across two
seeds, where 47/94 leaves seven unknown, but two preamble dibits per seed
remain unknown and the physical capture edge is unverified. A [96-symbol
stress test](g2/RECEIVER-MASK04-LONG-OFFSET.md) on a fresh seed now finds
five unknown data dibits across three ±7 Hz cases, despite zero incorrect
known decisions and a complete zero-offset control. Thus 46/93 is a useful
sampling hypothesis, not a complete offset-tolerant readout. Capture
additional executed visits around those unknowns, then test a frozen
phase-selection rule and the preamble/USART route on fresh streams. The
[two-pair long replay](g2/RECEIVER-MASK04-LONG-PAIR-UNION.md) finds that
46/93 and 47/94 complement one another on the repeated 96-symbol streams,
but a new four-case ±7 Hz seed leaves two data dibits unknown among 380:
both pairs abstain once and disagree once. Inspect those executed symbols
for a photo-compatible conflict/phase signal before another frozen holdout.
Keep C3 open rather than filling missing decisions or waiting for a
physical trace.
The [gap audit](g2/RECEIVER-MASK04-HOLDOUT-GAP-AUDIT.md) now captures
executed `3F8`/`3ED` bytes and ADC samples around those two symbols.
A later sample pair resolves the joint abstention but makes seven wrong
decisions elsewhere; at the preamble-to-data conflict, 46/93 is correct
and 47/94 is wrong. Derive any selector from executed state or a plausible
board circuit and freeze it before a new seed; do not add exceptions from
these inspected reference labels.
The [ADC-margin selector](g2/RECEIVER-MASK04-ADC-MARGIN-SELECTOR.md)
now freezes a simple signal-confidence rule: rank three executed capture
pairs by their minimum distance from the ADC midpoint over both symbols,
then use the first known frozen-table decision. On four new 96-symbol
±7 Hz streams it gives 0 wrong and 0 unknown among 380 measurable
dibits, while the earlier two-pair control leaves two unknown. This is
a successful **conditional readout**, not an identified Nokia circuit.
Constrain the capture/selector/USART route and challenge the rule on
additional phase, noise and controller-timing fixtures; keep C3 open.
The [offset zero-run handoff](g2/RECEIVER-MASK04-MARGIN-ZERO-HANDOFF.md)
now feeds the controller's actual scrambled eight-zero-octet streams
through four ±7 Hz real-PROM runs and the frozen margin readout. Each
recovers all 63 measurable dibits and eight line bytes; at the assumed
416-tick RxC rate, only the aligned external SYNDET pulse drives the
preserved 8031 ROM from `AF` to `B0`. The photos show the candidate ADC
and line-side USART packages but do not trace the inter-board serial
route. Continue testing its latch/selector, timing and sync source under
labelled assumptions; this conditional handoff does not close C3.

For C3, the [continuous preamble/data replay](g2/RECEIVER-MASK04-PREAMBLE-SERIAL.md)
recovers candidate dibits and a 2,400-bit/s serial schedule under labelled
ADC, readout and oscillator assumptions. Use the existing DSC and DSU photos
to propose pin-compatible `3F8`/`3ED` capture, phase-selection, RxD and RxC
routes. Model a baseline and meaningful alternatives, including external
SYNDET pulse timing and eight-bit character alignment, against the
continuous real-PROM trace. Record visible photo segments separately from
inferred connections, edges and dividers. An unsuccessful route rules out
that fixture; a successful route remains conditional until its physical
path and USART receive behavior are established. Keep C3 open and G2 active while those
tests or other independent C2/C4 experiments remain possible; do not wait
for continuity measurements or new photos to choose the next test.
The [`FF` sync-hunt screen](g2/RECEIVER-MASK04-SYNC-HUNT-ALIGNMENT.md)
is counterfactual for the controller's `CC` mode: the 8251A uses an
external SYNDET input, so `FF` fill cannot align its receiver internally.
The [external-SYNDET handoff](g2/RECEIVER-MASK04-EXTERNAL-SYNC-HANDOFF.md)
clocks the saved PROM-derived bits through an explicit receive-shift/RxRDY
model. Only a pulse before the first data bit reaches the controller's
`AF→B0` zero signature in its four tested fixtures; byte-early and
one-bit-shifted controls stay at `AF`. Treat the pulse source and timing
as hypotheses, not verified wiring or a C3 pass.

The [paced continuous-controller replay](g2/RECEIVER-TIMED-CONTROLLER-HANDOFF.md)
removes the immediate CPU-read handoff: at an assumed 416 8031 ticks per
receive bit, the uninterrupted ROM polls and consumes all eight bytes with
no overrun and reaches `AF→B0` only for the aligned pulse in four fixtures.
Its DTE selector must match the receive descrambler delay; the opposite
selector fails. The SYNDET source, physical serial route and naturally
timed Timer 1 behavior are still open, so keep C3 active.

The [executed A3→A4 frame edge](g2/CONTROLLER-A3-A4-MODE-EDGE.md) supplies a
specific next SYNDET hypothesis: decode the unique third-frame-byte `81→A1`
transition into a pulse before the first data RxC edge. Model the required
decoder, CD4094-to-receiver connection and timing as assumptions; the photos
do not establish those nets. The [instruction-level timing probe](g2/CONTROLLER-SYNDET-EDGE-TIMING.md)
shows the controller writes that frame 150/124 emulator ticks before its
first line-data byte in the call/answer fixtures; synthetic serial completion
means this is not a physical SYNDET timing measurement. Compare this candidate
with no pulse, an
unqualified bit-5 rise, and pulses one bit or one byte away, using the same
PROM-derived input and controller state. If the candidate misses the required
edge or the controller signature, revise the decoder or clock alignment and
continue with another photo-compatible route. Do not mark G2 blocked because
SYNDET continuity or the physical pulse timing is unknown.

The [controller zero-run handoff](g2/RECEIVER-MASK04-CONTROLLER-ZERO-HANDOFF.md)
now joins a longer real-PROM receive trace to the 8031's executed `AF→B0`
zero detector under a labelled USART byte handoff. It narrows the required
consumer behavior, but the external bit logic, byte clock and physical RxD
route remain hypotheses. Test those routes against the controller signature;
do not count the conditional handoff as a C3 pass or pause for new photos.
The [four-bit phase test](g2/RECEIVER-MASK04-FOUR-BIT-PHASE.md) gives one
frozen rule for the cardinal and diagonal carrier grids but finds genuine
same-input phase collisions between them. Keep its four photo-compatible
latch inputs as a baseline, add a second executed visit or retained state
to resolve those collisions, and test fresh intermediate angles before
repeating the serial/controller handoff. The failed intermediate-angle
fixture narrows the rule; it does not make uncertain wiring a goal blocker.
The [two-visit transition test](g2/RECEIVER-MASK04-TWO-VISIT-TRANSITIONS.md)
finds that Y6/Y7 at visits 47 and 94 carry enough information to separate
every observed dibit transition in the inspected traces. Its frozen
external lookup still leaves five fresh data transitions unknown. Keep
those as explicit missing cases, and test an executed or small
photo-compatible consumer of the two captures before treating this as a
USART bit route. The missing net trace does not pause that experiment.
The [phase-state audit](g2/RECEIVER-MASK04-PHASE-STATE-AUDIT.md) rules out
one tempting small consumer: a fixed phase label for each four-bit state
plus a constant symbol advance. Self-transitions force a 180° advance,
but an observed three-edge cycle contradicts that model. Seek direct
pair-to-dibit logic or additional retained/timing state; do not infer a
simple absolute-phase latch from the transition lookup.
The [direct Boolean transition screen](g2/RECEIVER-MASK04-TRANSITION-PLA.md)
fits the 86 observed keys with 17 product terms but misses 20/987
leave-angle-out decisions and two fresh data decisions. Treat those as
counterexamples to that fixed circuit, not as a reason to fill unseen
keys from reference answers or pause C3. Test richer executed features,
retained state or capture timing against new streams.
The [preamble phase-alias audit](g2/RECEIVER-MASK04-PREAMBLE-PHASE-ALIAS.md)
now limits one tempting selector for those readouts. Fresh real-PROM runs
show that the full 32-symbol preamble has identical `3ED` row-0/row-3 Y
and `3F8` Y triples at ADC visit 47 for 45° and 180° carrier rotations,
although the diagonal rule decodes data only at 45° and the nominal rule
only at 180°. A row-0 bit selector fails at 90°; a four-value selector
fails at 180°. Seek another visit, full-rate sample or retained phase state
before selecting the readout and replaying USART RxD. This collision does
not block C3 or prove a physical net.
The [two-visit preamble selector](g2/RECEIVER-MASK04-PREAMBLE-TWO-VISIT-SELECTOR.md)
finds the missing distinction at `3F8` Y7 on ADC visit 94 and combines
it with row-0 `3ED` Y at visit 47. Frozen before a fresh data seed, this
external rule recovers all 248 measurable preamble and 128 data dibits
across eight 45° grid rotations in eight 576,047-word PROM runs. It fails
all eight saved intermediate-angle challenges, so test an executed or
photo-compatible phase tracker/multi-visit consumer rather than promoting
the grid rule to C3. The selector clocks, logic and USART path remain open
wiring hypotheses; G2 stays active.
The [cubic transition constraint](g2/RECEIVER-MASK04-CUBIC-TRANSITION.md)
now extends the distinct four-bit two-visit transition readout: among 86
observed development keys, a frozen cubic Boolean relation forces 14
unseen labels. It resolves four of five unknown decisions on the saved
13-angle PROM challenge (0 errors, 1 unknown / 611) and all three
unknowns in three new-seed PROM runs at 0°/75°/165° (0 errors, 0 unknown /
141). The remaining `3C` key, arbitrary phase tracking, the external
logic and USART route stay open. Test another executed feature or visit
and a complete serial handoff; do not promote this conditional readout to
C3 or pause for missing continuity.
The [dual-feature consensus](g2/RECEIVER-MASK04-DUAL-FEATURE-CONSENSUS.md)
combines the two conflict-free four-bit captures from executed `3F8` Y
at ADC visits 47 and 94. Replaying all 13 held-out 0°–180° real-PROM
streams gives 0 wrong and 0 unknown among 611 decisions, with no
disagreement where both readouts know a label. The alternative subset
resolves the primary rule's `3C` gap without fitting that held-out answer.
This is a conditional external consumer, not a traced Nokia decoder;
test the latch/serial/USART handoff and new phase/data cases, keeping C3
open without waiting for continuity.
The [dual-feature zero-run handoff](g2/RECEIVER-MASK04-DUAL-ZERO-HANDOFF.md)
now runs two 768,047-word real-PROM receive traces at 75°/165° through
32 `11` preamble symbols and eight controller-scrambled zero octets.
Both recover all 63 measurable dibits and the exact eight line bytes;
the paced external-sync/8031 model consumes all eight without overrun and
reaches `AF→B0` only with the aligned SYNDET pulse. Early, late, absent
and opposite-selector controls stay at `AF`. This supports a conditional
DSC-to-controller behavior, but the five-bit capture, serialization,
clock, SYNDET source and physical USART path are still hypotheses. Test
photo-compatible latch/serial routes next; keep C3 open and G2 active.
For C2, the [joint-map PROM-edge replay](g2/JOINT-MASK04-TX-PROM-EDGE.md)
supports both candidate DAC latch phases under an assumed divided clock and
six photo-compatible bus orders. Their output codes differ, so neither phase
is a verified board route. Under the assumed bandpass, changing A2 codes
remain almost as loud as A1, whereas holding the last A1 code or forcing a
constant code settles to silence. Test a photo-compatible A2 hold, code
override or analog-mute control route rather than treating code 128 as the
only possible mechanism. Carry both latch phases forward; keep C2 open
without treating the untraced clock, DAC bus or line filter as a goal blocker.
The [executed A2 frame-bit screen](g2/CONTROLLER-A2-LATCH-GATE.md) now finds
one specific hold hypothesis: third-frame-byte bit 0 is high across A1/A3/A4
and low across A2 in both selector runs. If it drives the photographed
74LS373 latch-enable pin, the saved real-PROM hold case gives A2 silence and
preserves the later data decisions. The bit-to-latch connection is not traced
or a C2 pass.
The [controller gate timing](g2/CONTROLLER-A2-LATCH-GATE-TIMING.md) places its
A2 low interval at 61,938/61,772 modeled 8031 ticks, or about 596/594
candidate DAC samples. The [extended joint-map PROM run](g2/JOINT-MASK04-A2-LE-TIMED.md)
now carries the proposed hold through 74 A2 symbols and the first two/four
A3 samples, then through the real controller-derived A4 data. Both selectors
complete 2,040,256 instructions; all 72 bus/phase/release cases retain a
2,100 Hz tone, quiet late A2 and 0/62 A3/A4 decisions. This strengthens the
specific controller-to-latch hypothesis but leaves its net and analog route
unverified. Keep C2 open and test independent output-route constraints next.
The [photo-B5 single-bit test](g2/JOINT-MASK04-PHOTO-B5-TONE.md) checks the
one visible DAC input candidate against the same mask-`04` PROM mapping.
Full candidate codes peak at 2,100/1,800 Hz for tone/carrier controls, but
B5 alone peaks at 2,400/2,600 Hz in the tested band. Do not treat that pin's
changing level as proof of a line signal; pursue a higher-weight DAC input or
analog output node under labelled photo-compatible routes.
The [all-bit decomposition](g2/JOINT-MASK04-DAC-BIT-CONTRIBUTIONS.md) now
identifies the decisive higher-weight hypothesis in these same traces: at
the exact 2,100/1,800 Hz DFT bins, the assumed Y7→DAC code-bit-7 component
equals the full-code phasor and the other seven components are zero, across
six bus orders and both latch phases. Test the Y7/latch/DAC MSB route or an
independent analog constraint next. This digital result is not a physical
DAC/line connection and does not close C2.
The [MSB-only data replay](g2/JOINT-MASK04-DAC-MSB-DATA.md) extends that
constraint to the executed controller-derived A3/A4 streams: on the fixed
mask-`04` map, the assumed DAC top bit alone keeps the 2,100 Hz A1 peak
and gives 0/62 differential decisions for each selector, bus order and
latch phase after the same assumed filter. Lower seven bits alone miss
22–23/62. With the same two-basis raised-cosine fit, top-bit-only output
also scores R² 0.909/0.900 in call/answer, above the full-code bus ranges
0.834–0.838/0.810–0.815. Focus the next photo-compatible route test on
Y7 through the sample latch to DAC08 B1/pin 5 and the analog output;
keep C2 open until that route and the line signal are independently
established. The existing photos do not settle the back-side continuation.
The [joint-map free-clock screen](g2/JOINT-MASK04-FREE-CLOCK-MSB.md) now
tests a simpler periodic latch at each of `127`–`12A` on the same two
controller-derived 1,248,256-word PROM streams. All four phases, six
DAC bus orders and both selectors keep the 2,100 Hz A1 peak and 0/62
A3/A4 decisions with either full codes or Y7/MSB alone. Their byte
hashes differ, so the signal metrics do not identify the physical edge.
The 375-PROM-edge divider is not required for this conditional result;
test an independently constrained clock or analog node next and keep
C2 open without waiting for a new photograph.

**Goal G1:** get the four-PROM control store (810237C–810240C) running in an
emulator without errors, so that we can read what the microprogram does.
Bit-exact fidelity to the Nokia board is *not* required. Where the hardware is
unknown, the emulator takes an explicit, labelled assumption and keeps going
instead of stopping.

This replaces "trace every net first" as the way forward. The earlier attempts
([illustrative map](history/ILLUSTRATIVE-RUN.md), [photo-only board model](board/README.md))
blocked on wiring that the photographs cannot supply. The PROM contents turn
out to constrain the sequencer fields well enough to proceed without it.

## Starting point: fields recovered from the PROM data

These come from statistical and structural analysis of the dumps only. No net
was traced. Bit names are `chip.bit` using physical board positions and PROM
data-bit numbers. Address wiring is assumed straight through (sequencer
address N = offset N in all four files), which the results below support.

| Field | Bits | Status |
| --- | --- | --- |
| 8X02 command | AC2 = 17.0, AC1 = 17.1, AC0 = 17.2 | Strong |
| Branch address B0–B9 | B0 = 11.0, B1–B8 = 10.7 … 10.0, B9 = 18.7 | Strong for B1–B8; B0/B9 good, one outlier |
| Condition select | 17.4–17.6 (3 bits) | Probable |
| "Address from microword" flag | 17.7 | Probable |
| A 4-bit register-number field | LSB-first 18.1, 18.0, 17.7, 17.6 | Tentative; overlaps the two rows above |

Evidence:

- **Command histogram.** Of 1021 used words: INC 639, BRT 130, POP 88, BSR 87,
  TSK 33, PLP 22, BLT 22, RST 0. Push-for-loop and branch-to-loop counts match
  exactly. Address 000 begins INC, INC, INC, BRT; the old "POP with an empty
  stack at 001" was an artefact of reading the command from chip 10.
- **Unused words.** Only 1DF, 29F and 3FF are `FFFFFFFF`. 1DE is a branch with
  condition select 0, and 29E and 3FE are POPs, so all three follow an
  unconditional transfer.
- **Branch address.** Words that follow a POP and cannot be reached by a skip
  must be branch or call targets (85 of them). The chosen field was the best of
  every contiguous 10-bit window over all chip orders, both bit directions and
  both polarities, and a per-bit greedy refinement could not improve it. It
  covers 33 of the 85; the other 52 are almost all dispatch-table entries (see
  below), which no microword address can reach.
- **Subroutine shape.** Of 39 distinct BSR targets, 38 run linearly to a POP
  with balanced PLP/BLT. Example: 1E9 is `PLP, BLT, POP`, called 12 times, each
  time after a `01 36 .. ..` setup word. The outlier is 01E, which starts with
  a BLT.
- **Condition select.** BRT uses select 0 with 17.7 set in 78 of 130 words
  (unconditional jumps) and selects 1–7 for the rest. BSR is select 0 with 17.7
  set in 77 of 87. TSK uses all eight selects.
- **Computed dispatch.** The other ten BSR words are `00 80 01 3c` /
  `00 80 03 3c`: address field zero, 17.7 clear. Six stand directly before
  4 × 4-word tables whose groups each end in POP (for example 3C2 before 3C5,
  3C9, 3CD, 3D1). 08A–099 is a table of 16 one-word POP entries. These read as
  calls whose target comes from data, probably through the buffer at U4 that
  trace fragment F001 (U9 pin 17, B3) runs toward.
- **Bit order.** The register-number field counts 0–15 across those tables in
  the order 18.1, 18.0, 17.7, 17.6. Together with the reversed chip 10 address
  byte, this says the microword is laid out MSB-first relative to PROM data-bit
  numbering. Expect other fields to be contiguous in that reversed order.

Not yet known: the dispatch address source and table bases, what condition
selects 1–7 test and their polarity, and every Am2901 field (I0–I8, A, B,
carry-in, D source, shift linkage). In non-branch words chip 10 is mostly
`01`, `15`, `00`, `05`, so it carries something other than an address there.

## Working rules

These rules remain in force for G2 in [PLAN-2.md](PLAN-2.md) and subsequent
reconstruction work; completing G1 does not retire the assumption-driven approach.

- Every assumption lives in a mapping, candidate board configuration or scenario
  file with a status (`recovered-from-data`, `hypothesis`, `stub`), never
  hard-coded in the model.
- Unknown inputs become explicit scenario parameters with logged values or
  remain unknown in a diagnostic run. Never silently replace wiring, RAM or inputs with
  zeros. A run that completes is reported as "runs under these assumptions",
  not as faithful Nokia execution or proof of modem function.
- Raw dumps and photographs stay untouched. Each step lands with tests and a
  checked-in result summary, as in the existing experiments.

### Uncertainty is a reason to experiment, not a goal blocker

Missing pin traces, uncertain clock phases, unidentified signal sources and
unavailable continuity measurements **do not by themselves block progress**.
Use the photos, component topology, chip behavior, ROM structure and existing
traces to propose plausible connections, then run them. Physical checks are
optional ways to discriminate candidates, not prerequisites for continuing.
For each uncertain connection, record the visible photo evidence and the
assumed continuation separately. Run the simplest pin-compatible candidate
with the real PROMs, then vary the few connections or timing choices most
likely to change the outcome. Compare against a control using the same input
and startup state. If the candidate fails, record what that fixture excludes
and choose the next candidate or independent program/signal test. If it works,
report the result as conditional on the assumed wiring; do not promote it to a
verified board connection or a passed acceptance check.
**Status rule:** report G2 as active with the current uncertainty and the next
bounded experiment whenever a photo-supported connection, timing or input
hypothesis can still be tested. A failed run closes that hypothesis under its
recorded fixture; it does not block G2. Reserve "blocked" for the case where
the available evidence supports no runnable candidate and no independent
controller, PROM or signal analysis can advance an acceptance check. Before
using that status, record the candidates already tried, why each remaining
avenue cannot run, and the exact outside input needed. An unverified physical
connection by itself never satisfies this rule. Do not ask for more photos or
continuity measurements as a prerequisite while executable routes remain open.

Do not convert an unmet acceptance check into a goal blocker: keep its status
open, record which physical claim is still unverified, and run the next
candidate. A measurement can distinguish surviving models later; its absence
does not stop tests that can be run under explicit assumptions now.

**Default decision:** keep the goal active and run a photo-compatible baseline
plus a few meaningful alternatives whenever a connection is uncertain. Mark
only the tested candidate as unsuccessful when it fails; do not mark the goal
blocked or request new measurements while another runnable hypothesis or
independent program/signal analysis remains. State the next experiment in the
result summary so an ambiguous photograph leads to another action.
An acceptance check that has not passed is **open**, not automatically blocked.
If the photos show only part of a required net, assume the simplest
pin-compatible continuation, label the unseen segment and its timing, and run
the microprogram with the real PROMs. Test alternatives where they could change
the result. A plausible output is a conditional finding, not proof of the
physical connection or a passed acceptance check. A failed candidate prompts
another assumption or independent experiment; missing continuity alone never
pauses the work.
For the current receive/echo work, infer candidate ADC, feedback and mode-control
routes from the existing photographs and executed controller state/frame timing.
Label each inferred connection and training/freeze gate, run a small set of
alternatives with the real PROMs, and compare against zero-input, remote-only
and own-echo controls. If a candidate fails to recover bits or attenuate echo,
record its exact fixture and try another route or mode timing. Do not claim a
physical wire, echo-canceller function or C3/C4 pass from a plausible output
alone; do not call the goal blocked merely because those checks remain open.
For each unresolved connection, start from the visible pins, chip directions
and nearby parts in the existing photographs. Draw the shortest plausible
continuation as a labelled hypothesis, including any required inversion,
latch edge and clock ratio; add a small number of alternatives where those
choices change the result. Run each with the real PROM contents and relevant
8031 traffic, and keep the mapping, stimulus and output trace together. If a
candidate explains the expected behavior, report that behavior as conditional
on its wiring and timing. If it fails, revise or discard that candidate and
continue with another testable route. Physical continuity is useful later to
choose among survivors; it is not a prerequisite to running or interpreting
them, and a missing net trace alone must never be recorded as the G2 blocker.
Before rejecting a candidate, compare it with a control under equivalent
input levels, register addresses and startup state. A split-slice run must
state any high-slice pin levels separately from the low slice; copying a
diagnostic level between them is a labelled hypothesis, not a traced wire.
If unequal fixtures explain a failure, correct the fixture and rerun the
candidate. The untraced connection remains an experiment, not a blocker.
This also applies when the controller emits no line-data bytes or a candidate
route fails to reproduce a required signal. Use the protocol's specified
symbol sequence and the observed controller state/frame timing to define a
labelled idle-source or decoder hypothesis, then run it continuously into the
next state with the real controller bitstream. Compare a simple control input
and inspect the transition, phase and output samples. A match constrains the
candidate route; it does not establish the untraced source or physical line
connection. If it fails, revise the source, gate, timing or loop and keep G2
active while another bounded experiment remains.
Check package pin counts and pin directions before turning a visible track into
a wiring hypothesis. If a later check changes the interpretation of a photo,
correct the evidence record and relabel earlier simulations as counterfactual
tests; keep useful results, but do not treat them as validation of the revised
connection. Then test the revised route or move to another independent clue.

**Current G2 decision:** the ambiguous PROM-to-latch, latch-to-Am2901 and
Am2901-to-DAC connections are open hypotheses, **not a goal blocker**. The
photographs may justify a candidate even when they do not prove its endpoint.
For each candidate, record the visible segment separately from the assumed
continuation, encode it as a labelled scenario, and exercise it with the real
PROMs and controller inputs. Keep a negative result tied to that exact wiring
and state fixture. If a sweep only yields fixed output or a wait loop, change
the connection, timing or input fixture, or move to an independent controller,
ROM or analog-path constraint. This applies equally to uncertain upper-slice
instruction fields and to the DAC input path: a missing pin-level trace does
not halt implementation or analysis. Do not wait for new photos or continuity
measurements to make the next move, and do not promote an assumed connection
to a board fact just because it produces a plausible run.

For the current transmitter test, apply the same rule to the untraced
8251A TxRDY/TxD-to-DSC input gate and DSC-to-DAC latch, bus and clock. The
photographs and executed controller traffic are enough to define candidate
routes; exact net continuity is not a prerequisite for running them. Start
with the observed A1/A3/A4 frame changes, the 8251A `FF` sync fill and the
TxRDY-paced nine-byte stream. State each assumed gate, bit alignment and DAC
sample rule, then run tone, segment-1 reversals and segment-2 data through one
uninterrupted real-PROM trace. Compare it with nearby bit offsets and simpler
control inputs. A match advances a *conditional* transmitter explanation;
the line waveform and physical routing remain separate acceptance evidence.
If the candidate fails, revise the gate, timing or output route and continue
with another bounded test. Neither outcome makes missing continuity a goal
blocker while runnable candidates or independent analyses remain.
The [D349 source-update experiment](g2/PHOTO-TABLE-SOURCE-UPDATE.md) is a
concrete example: after two restart fixtures gave fixed table sources, four
other photo-compatible scenarios found an input-sensitive R5 write before
later table calls. That conditional path is a lead to test with changing
inputs, not a claim about the board's untraced wiring.

**Current G2 application:** the [joined CD4094/frame/line replay](g2/PHOTO-CD4094-FRAME-LINE-JOINT.md)
tests each simple chip/Q-pin byte orientation with the real controller frames
and line bits. It finds that the apparent branch split depends on the assumed
frame lane and reaches no candidate output word. The
[paired A0/A1 state replay](g2/PHOTO-CD4094-STATE-TONE.md) finds a runnable
state-selecting lane, but its held alternate-chip bytes do not give the
proposed 2,100 Hz phase step. The
[controller P1 replay](g2/CONTROLLER-STATE-PIN-CHANNELS.md) also shows that
P1.5 distinguishes A0 from A2 even when their serial frames match; keep it
as a separate, untraced input hypothesis in the next state-sensitive test. The
[second-loop ROM liveness test](g2/PHOTO-12C-ROM-LIVENESS.md) shows that the
ROM-bank effect is erased by `12D` in the tested q3 loop, so a candidate DAC
latch must sample before that point. The
[A0/A1 edge screen](g2/PHOTO-12C-PROM-EDGE-LATCH.md) finds a raw U18 D1
edge at every A1 `12E` visit but not in the recurring A0 loop; test a
labelled divider/clock route rather than treating that correlation as a
traced DAC strobe. The
[divided-strobe A1 test](g2/PHOTO-12C-DIVIDED-STATE-LATCH.md) finds no
2,100 Hz peak from the three direct held frame bytes under oscillator divisors
1–4 and every tested divider alignment; keep decoded or changing inputs and
other output paths live. The
[A1 bit-swap candidate](g2/PHOTO-CD4094-BIT-SWAP-TONE.md) now gives a
labelled two-wire alternative: exchanging candidate D0/D3 sends A1 to a
2,100 Hz PC129 phase walk at one tested divider ratio, but the clock and
full DAC bus remain untraced. Its raw PROM edges are not mode-isolated, so
test a qualified latch before promoting the signal claim. The
[bit-swap byte-source screen](g2/PHOTO-CD4094-BIT-SWAP-DATA-SITES.md) finds
that the selected ROM byte does not give a dominant 2,100 Hz upper-bank
full-byte stream; the stronger `12A` result is almost just the phase ramp.
Keep the DAC byte route and shaping stage open hypotheses. The
[photo-B5-compatible full-bus screen](g2/PHOTO-DAC08-BUS-ORDER-SCREEN.md)
shows that a 2,100 Hz B5 bit can coexist with a different full-code peak
under three simple LS273-to-DAC08 orders. Carry the complete candidate DAC
byte and clock through later tests. The
[main-frame carrier swap](g2/PHOTO-MAIN-FRAME-CARRIER-SWAP.md) supplies a
separate 1,800 Hz lead: one candidate CD4094 byte is `A1` in all four real
8031 main-loop classes, and a labelled D0/D4 crossing makes it D127=`B0`.
The upper-bank, divisor-1 run gives a full candidate DAC-code peak at
1,800 Hz, but no USART dibits or physical DAC clock are yet coupled. Test
the symbol path rather than treating the missing wire as a blocker. The
[line-rate D127 hold](g2/PHOTO-MAIN-FRAME-LINE-HOLD.md) feeds actual 8031
USART bits on two hypothesized D lanes. It produces retained 64/128-step
phase changes but also changes the candidate DAC-code frequency during each
held one bit. Keep testing a photo-compatible timed or decoded input route,
without calling this direct gate the modulator. A
[four-visit dibit-pulse replay](g2/PHOTO-MAIN-DIBIT-PULSE.md) now tests one
counter/parity-qualified alternative with real USART dibits. Four continuous
PROM runs retain all four Gray-related quarter-cycle phase offsets while
holding the carrier step outside each pulse. Its pulse gate, DAC clock and
shaping path are untraced, and the full-stream candidate DAC spectrum differs
from the reference in one controller class. Test alternate output/phase
routes; this is a conditional lead rather than a C2 transmitter pass. The
[DAC bus/decoder screen](g2/PHOTO-MAIN-DIBIT-DAC-DECODE.md) finds that one
simple photo-B5-compatible full bus lets an independent reference receiver
recover 103/104 real controller dibits, versus 30 or more errors under each
of its five other simple orders. The later
[exhaustive bus screen](g2/PHOTO-DAC-BUS-PERMUTATIONS.md) finds 12 zero-error
orders among all 5,040 photo-B5-compatible permutations, so that byte order
is not unique. This supports conditional phase information, but
the pulse gate, latch clock, line route and DSC receive/echo path remain
unverified. The original dibit score uses first-serial-bit-low numeric
labels; the later [standard segment-2 calibration](g2/PHOTO-SEGMENT2-STANDARD-CALIBRATION.md)
finds that exchanging the candidate two-bit pulse lanes gives zero
standard-labelled phase errors for the controller's exact GPC/GPA pattern.
This is a stronger conditional synchronization result, not a traced line
output. The
[joint state/data bus check](g2/PHOTO-STATE-DATA-BUS-COMPATIBILITY.md) shows
that the separate A1 2,100 Hz and main-frame 1,800 Hz bit-swap leads cannot
share one fixed chip-1 pin permutation, even with fixed inversions. Test
mode-dependent selection or another source before combining them into a
single transmitter interpretation. The
[controller mode-decode replay](g2/PHOTO-CONTROLLER-MODE-DECODE.md) tries a
fixed fan-out/inverter candidate, then checks preserved 8031 frame history.
The preserved chain emits chip-1 `A1` during its A1 state, where the isolated
send fixture emitted `81`; a byte's counter-phase bit cannot be treated as
a state-only tone selector. Continue with time-varying controller frames and
separate DAC hypotheses, without blocking on physical net ambiguity. The
[A1 counter-phase replay](g2/A1-COUNTER-PHASE.md) now locates the discrepancy:
the main loop sets flag24.5 before its first A1 output build, yielding `A1`
and reloading counter49, while the isolated fixture starts with that flag
clear and yields `81`. A directed preserved-state replay later yields `81`
and `C1` as the counter advances. An uninterrupted polling-loop fixture held
in A1 now emits `A1` for eleven iterations, then `81`, in four controller
selector classes. The [dynamic A1 mode replay](g2/PHOTO-A1-DYNAMIC-MODE-REPLAY.md)
feeds that byte change into one continuously running, photo-compatible DSC
scenario; its candidate DAC-code peak moves from 1,800 to 2,100 Hz in all
four classes. Test dibit phase modulation in the same run and the
timer-driven A1 duration. The decoder, DAC bus and clock remain hypotheses;
no new photograph is needed to run those candidates. The
[line-rate hold test](g2/PHOTO-127-LINE-RATE-HOLDS.md)
also shows that raw USART bits at D12C leave the proposed phase loop before a
sustained 2,400-bit/s stream under four assumed clock divisors. Treat that as
a rejection of the **raw-bit fixture**, not of every controller-to-DSP route.
Next try a decoded or biased bit input, a different clock/loop, or a stateful
ROM consumer, with the DAC latch route and sample gate stated separately. Compare
command-dependent samples against the required 1,800/2,100 Hz and dibit
behavior. Continue independent receive-path analysis through the
[D3F8 stream path](g2/LOWER-I-STREAM-SCHEDULE.md). Record each result and its
next discriminating experiment; do not wait for a complete pin trace.

The [transmit PROM-edge phase check](g2/PHOTO-TX-PROM-LATCH-PHASE.md) adds a
specific latch-clock hypothesis to the joined DAC path. Real U10 D2 rises
at the ROM-result words `129/12E` and falls at `12A/12F` in both four-word
loops. A direct rising-edge 74LS273 clock may see the preceding Y byte;
a qualified later/inverted edge can see the settled ROM-result byte if its
setup timing is met. The latter phase fits the saved full-PROM pulse-shaped
reference better for all six surviving candidate DAC buses, but the edge
wire, inversion, divider and full DAC bus remain assumptions. Run a
rate-qualified post-ROM latch scenario next; do not mark C2 passed or G2
blocked on this timing ambiguity.

The [divided PROM-clock replay](g2/PHOTO-TX-DIVIDED-PROM-CLOCK.md) now runs
that latch hypothesis through both uninterrupted controller-driven PROM
traces. Dividing 312,054 real U10 D2 edges by 375 gives 832 evenly spaced
candidate samples per mode; the captured byte hashes match the prior
full-PROM site streams. Both direct-rise and inverted-fall phases keep the
2,100 Hz peak, A2 silence and 0/744 data decisions under the same assumed
bandpass and six candidate buses. The direct-rise phase fits the tone better,
while the post-ROM phase fits the pulse-shaped data better. Use that tradeoff
to test an independently constrained clock phase or analog response; keep
C2 open and do not wait for a measured net before trying another candidate.
The [mask-`04` joint-map edge replay](g2/JOINT-MASK04-TX-PROM-EDGE.md)
confirms that this raw PROM strobe and its 832 divided captures also run
on the fixed map used for the receive experiments. The `129` capture hash
matches its saved full-PROM transmit run, but the mapped DAC-code hashes
differ from q3 and both latch phases have the same tested filtered scores.
Carry both photo-compatible phases into the next output-route test; do not
use the q3 waveform-shape preference to select a phase on mask `04` or
declare C2 passed without a constrained DAC/analog route.

The [cycle-divisor screen](g2/PHOTO-TX-CYCLE-DIVISOR.md) keeps the joined
transmitter fixture fixed and runs real-PROM traces at four hypothetical
`14.4 MHz / k` microinstruction rates. Only `k=1` retains both the A1
2,100 Hz peak and zero filtered A3/A4 dibit errors; the others shift the
tone and lose decisions. This narrows the assumed cycle budget, not the
untraced physical divider. Keep C2 open and continue with a photo-compatible
clock, input or receive-output candidate.

For each unresolved dependency:

1. Record what is observed, what is inferred and what must be assumed. Keep
   candidate connections separate from the verified evidence ledger.
2. Choose a reasonable baseline and a small set of meaningful alternatives;
   there is no requirement to enumerate every possible wiring permutation.
3. Make those choices configurable and run bounded, reproducible experiments
   with the real dumps. Select stimuli that exercise the disputed connection.
4. Compare initialization, control flow, stack behavior, I/O and signal output.
   Record which candidates fail, which remain possible and what the experiment
   cannot distinguish. Revise the assumptions or pursue another useful path.

**A stopped simulation is an experimental result, not a blocked goal.** An
unknown branch bus can stop one diagnostic run while explicit candidate bus
sources are tested in others. Repeated failures under one set of assumptions
are grounds to change the experiment, not to wait for measurements. The
[photo-informed board experiment](board/PHOTO-HYPOTHESES.md) demonstrates this
approach with executable candidate wiring and a targeted indirect-branch pulse.

Operationally, when a candidate reaches a wait loop, produces a fixed output or
misses a required path, close out **that run** with its exact assumptions and
trace. Choose the next photo-compatible connection, clock phase or input/state
fixture and state what observation would distinguish it. If the current batch
cannot discriminate candidates, switch to another independent analysis of the
controller, PROM or analog signal path. Keep the goal active while any of these
experiments can still advance it; do not turn an unverified connection into a
goal-level blocker merely because the first assumption failed.

For G2, treat a connection suggested by the available board photographs as a
testable candidate even when a trace disappears beneath a component or its
destination pin is ambiguous. Record the visible segment and the inferred
continuation separately, encode competing continuations when they affect the
result, and run the microcode under each. Do not wait for new photographs or
continuity measurements before trying those candidates.

Apply this directly to the output path on DED 3558. The photographed DAC08HP
and nearby 74LS273 identify a plausible byte latch and converter, while the
data-bit order, latch clock and route to the line remain uncertain. Start with
the pin-compatible connection and clock hypotheses that the photos support;
capture their candidate DAC input bytes during real-PROM, controller-driven
runs, then vary the disputed routes and sample phases. If none yields the
expected changing, command-dependent samples, investigate another mapping or
state source. Do not pause G2 for a complete pin trace, and do not call a
candidate byte stream the physical line output without independent support.

The Am27S31 A8 bank select is a current example: the photos do not establish
its source, but the lower- and upper-bank runs at 12C and the D127 ROM walk
behave differently ([12C comparison](g2/SWAPPED-ROM-LOOPS.md),
[D127 comparison](g2/PHOTO-127-BANK-COMPARE.md)). Treat fixed and changing A8
values as labelled scenarios, with any assumed timing or driver made explicit.
Run the next bounded controller-driven test under those scenarios and compare
ROM addresses, retained state and output bytes. If none produces the required
signal path, change the address mapping, timing or state fixture and continue
with another independent clue. Do not wait to trace A8 before testing, and do
not promote a useful bank choice to a traced connection.

Apply the same rule to the current execution dead ends. A run that parks in a
wait loop or misses the transmit path under one assumed latch route, dispatch
source, clock phase, input level or initial register/RAM state characterises
**that fixture**, not the whole reconstruction. First check the reachable
alternatives suggested by the photos and the ROM, vary disputed inputs and
starting states in a bounded sweep, and feed in the real controller commands
and bitstream where the proposed interface permits it. Keep the exact mapping,
stimulus, trace and negative result so a later physical check can distinguish
the candidates.
Continue with independent program and signal analysis while any connection is
unresolved.

When a photo-derived route involves a PROM enable or latch, test *when* each
value is sampled as well as which pins connect. Keep a same-phase case that
obeys the component's read conditions, and label other enable-level runs as
diagnostics unless an explicit hold or two-phase circuit can supply their
PROM data. For the candidate U10 E2→U5 and U11 E4→U6 routes, sweep plausible
latched levels and startup states, then test any surviving paths with the real
controller stream and ROM. A path that opens only while U10 is disabled is a
lead for a timing model, not evidence that the board uses that impossible
same-phase combination. If a case settles to fixed output, record the scope
and pursue a different phase, mapping, input route or state source.
The [stateful U5 clock screen](g2/PHOTO-TABLE-CLOCKED-U5.md) applies that rule:
seven raw PROM edges preserve the reached sign-table and consumer levels, but
none reproduces the full reference trace or a controller-dependent output.
That excludes those direct-edge fixtures, not decoded or external clock
phases; continue with a labelled alternative and a DAC-latch check.

An unknown physical net is never, by itself, a G2 blocker. If the available
photo-compatible candidates all fail, record what each run excluded and pivot
to a new mapping, timing model, stimulus or independent program/signal clue.
Keep the status **active, with the relevant acceptance check open**, while any
such experiment remains. Only consider a goal-level blocker after showing
that no available experiment can advance the acceptance checks. Before calling
something blocked, write down the concrete next experiment attempted, its
result and why no alternative candidate, stimulus or independent analysis
remains. A failed candidate or a missing continuity measurement does not meet
that test.

Apply this rule to the U9 enable/address-bus idea as well. A hypothesised
external driver can be modelled from the chip's documented pin behavior and
the photographed board, even though its Nokia wiring is untraced. Run the
candidate with the real PROMs, record exactly which address, input levels and
timing were assumed, and treat a return to `084` or a model stop as the outcome
of that fixture. The [one-cycle BRT vector screen](g2/BOARD-VECTOR-SCREEN.md)
does this for 76 candidate entry words. Its negative result directs the next
controller-input or timing experiment; it is neither a reason to block G2 nor
proof that address takeover is the physical control path.

This policy changes how we make progress, not the acceptance criteria. Keep
G2's transmitter and receiver/echo-canceller checks: completing a candidate run
does not satisfy them. Do not inject the expected waveform, force control flow
past a wait loop, or relabel an assumption as evidence to claim success.

The [eight-visit D3F8 screen](g2/LOWER-I-FOUR-SAMPLE-BIT-SCREEN.md) is the
current example of this decision. One photo-compatible, D0-only `08/09`
candidate carries all 128 controller bits through the selected ROM loop when
each bit is held for eight loop visits. Its input route and 153.6 kHz
microcycle interpretation remain assumptions. The
[alternating-visit latch screen](g2/LOWER-I-ALTERNATE-VISIT-LATCH.md) then
finds constant codes for held `08` under every tested direct Y/R10/ROM byte
route, so those routes cannot supply a held-input carrier at that clock.
Change the latch route, timing or command-dependent input fixture next;
a missing continuity measurement does not pause the experiment.

Apply the same rule to the photographed ADC0800 receive candidate. Its
complementary output bus, D3F8 input connection and sample clock have not been
traced, but the [held-input D3F8 test](g2/LOWER-I-D3F8-HELD-HISTORY.md)
shows a real-PROM loop that selects an assumed input and retains its history.
Use the available photos and component behavior to define a few explicit
ADC-bit, polarity, bias and clock hypotheses. Feed continuous reference
samples through each candidate, compare a changed or time-reversed stream
with a control that has the same later input, and inspect branch decisions,
retained state and any candidate receive output. An exit or fixed output
rejects that fixture; it does not block G2. If no candidate produces a
receive decision, revise the mapping or timing and pursue another independent
signal-path clue. A recovered bit supports only a conditional receiver
explanation until the physical input route is verified.

The [two-row sampled-state DPSK screen](g2/RECEIVER-TWO-ROW-SAMPLED-STATE-DPSK.md)
tests a fixed readout on the sustained 0/2 ADC fixture: its best training
choice has 1/36 training, 5/48 holdout and 11/48 fresh-validation dibit
errors. This is input-sensitive receiver state, but not a recovered decision
path. Keep C3 open and test a stateful readout or another photo-compatible
clock/route; the untraced connection is not a blocker.

The [matched-last-level order test](g2/RECEIVER-TWO-ROW-ORDER-MEMORY.md)
further narrows that state: reversing `19,A9` holds changes the late state,
but two equal-histogram three-hold sequences with the same final `A9` hold
reconverge before the common tail. The long-lived offset in this fixture is
therefore not evidence by itself of multi-sample phase history. Seek a
sample-combining update or executed decision output next.

The [3EB ADC bus-hold screen](g2/RECEIVER-3EB-ADC-ROUTE-SCREEN.md) tests
another photo-compatible ingress assumption. The wrapper word also selects
external D under the joint mapping; feeding full complementary ADC bytes
there makes a 32-sample waveform leave the receive loop after 282 `3F8`
visits, while the `3F8`-only run completes 3,000. A held `A9` at `3EB`
leaves before the first `3F8` visit. This rejects the direct full-byte
wrapper hold under that mapping, not a separately gated ADC route. Vary
the enable/bit lanes and inspect an executed decision or output site.

The [3EB nibble truth screen](g2/RECEIVER-3EB-NIBBLE-TRUTH.md) resolves that
lane question under the current joint map. All 256 first-wrapper D bytes
collapse to 16 high-nibble classes; low-nibble-only feeds at either or both
wrapper visits leave the entire 32-sample trace unchanged. Full-byte feeds
at either visit still exit early. Thus a low-nibble gate is a no-op here,
not a receive advance. Change the high-slice timing/condition, dispatch or
output hypothesis next instead of widening that inert lane test.

The [raw-PROM ADC-enable phase screen](g2/RECEIVER-PROM-ADC-ENABLE-PHASE.md)
provides a concrete connection hypothesis: a one-cycle-delayed decode of
`!U10.D1 & U10.D3 & U10.D7` enables the candidate ADC byte at every `3F8`
visit without also feeding it to wrapper `3EB` or high-slice `3FA`. Its
3,000-visit trace matches the earlier PC-qualified fixture, but the decode,
latch phase and buffer wiring are still assumptions. The
[wrapper decision probe](g2/RECEIVER-WRAPPER-DECISION-PROBE.md) finds no
ADC-dependent TEST, branch, Y or ALU flag at `3EA`–`3ED` when comparing a
changing-dibit waveform with an all-zero-dibit control, even though Q changes
at 4,137 visits to each wrapper word. The two reached table rows have
input-dependent Y and flags but no changed TEST or branch; prior fixed-phase
flag screens do not decode the dibits. Keep C3 **open and G2 active**. Test
where row arithmetic or Q/RAM state is latched for an output, then exercise
a photo-compatible route to USART 01 RxD. If that readout fails, revise
the enable phase, dispatch source or output route and run the next bounded
candidate; do not wait for a continuity measurement to proceed.

The [four-row condition screen](g2/RECEIVER-FOUR-ROW-CONDITION.md) tests a
counter-like `0→1→2→3` dispatch instead of assuming that the 0/2 diagnostic
is the board schedule. Five labelled TEST flag choices sustain 1,500 ADC
visits across all four rows. In one full-row waveform pair the ADC changes
the third-row ROM address on 1,359 visits, but under the then-selected
lower-field mask `08` the fourth row makes complete RAM/Q state identical to
the control on all 1,500 visits. Keep that fixture as
a conditional transient-input candidate, not a recovered receiver. Test a
third-row latch or a different dispatch/condition route next; do not treat
the absent pin trace as a blocker.

The later [joint mask-04 screen](g2/JOINT-FOUR-ROW-RETENTION-TX.md) changes
one disputed lower instruction source and retains the ADC-dependent state
after the fourth row on 1,312/1,500 paired visits and four fresh nonperiodic
streams. The same fixed map still gives both modeled controller-driven
transmit modes a 2,100 Hz tone and 0/62 filtered data errors across six
candidate DAC buses. This replaces mask `08` as the stronger joint hypothesis;
its [direct retained-bit screen](g2/RECEIVER-MASK04-RETAINED-BIT.md) has no
exact training fit, so C3 remains open. Continue with a stateful decision or
photo-compatible output path rather than waiting for net continuity.
The [executed arithmetic check](g2/JOINT-MASK04-ADC-ROM-WRAPPER-RULE.md)
shows the candidate ADC byte entering a `3F8` calculation, selecting a
real-ROM byte at `3F9`, and Q's low nibble reaching R1 at `3EB`, then Y
at `3ED`. The
[fixed-phase quadrature screen](g2/RECEIVER-MASK04-QUADRATURE-DECISION.md)
does not turn that retained state into a received dibit. Keep testing an
executed decision/output route under labelled photo-compatible connections;
neither missing continuity nor a failed readout blocks G2.
The [mask-04 PROM-latch candidate](g2/RECEIVER-MASK04-3ED-PROM-LATCH.md)
now supplies one all-positive raw-PROM decode that would clock R1-derived
`3ED` Y after every row. Eleven full traces verify the edge, but their
captured bytes yield no exact fixed-phase direct bit. U19/U12 wiring and
USART RxD remain hypotheses; test a stateful readout next.
The [paired-row phase-code test](g2/RECEIVER-MASK04-ROWPAIR-PHASE-CODE.md)
finds a compact, generalizing state in those executed bytes: a fixed
eight-state lookup of row-0/row-3 `3ED` Y pairs gives zero differential
dibit errors on 36 training, 48 holdout and 48 fresh decisions under the
labelled mask-`04` receive fixture. The lookup and subtraction are external;
find a photo-compatible or executed consumer and its USART timing before
claiming C3. Test another input level rather than treating the untraced
consumer as a blocker.
The [changed-level check](g2/RECEIVER-MASK04-ROWPAIR-LEVEL-CHECK.md) now
does that input test: a 0.75-gain, unclipped reference waveform remains
decodable, but the frozen eight-state lookup recognizes only 2/24 paired
transitions and gets both wrong. Seek an executed threshold/gain-control
consumer or a generalizing stateful decision; do not treat the original
0/96 error result as a C3 pass.
The [row-3 parity-gate replay](g2/RECEIVER-MASK04-ROW3-PARITY-GATE.md)
finds one fixed, simpler survivor: OR of `3ED` row-3 Y bits 0–2, XORed
with the previous symbol's value, matches dibit-bit parity on 192/192
transitions across nominal, reduced-gain and biased full-PROM runs. The
same gate on raw ADC misses 103/192. This is an executed-byte lead for
one bit combination, not an executed or routed USART decision. Test a
photo-compatible row-3 consumer and the second independent bit; keep C3
open and G2 active.
The [phase-47 Boolean readout](g2/RECEIVER-MASK04-PHASE47-BOOLEAN-DIBITS.md)
now recovers both reference dibit bits with 0/96 errors on eight fresh
full-PROM traces spanning nominal, 0.75/1.25 gain and +16 PCM bias. It
uses two executed `3ED` Y bytes, but its row-0 hold, row-3 gates,
previous-symbol phase register and USART timing are external hypotheses.
Run a photo-compatible latch/consumer next; keep C3 open until the
recovered bits reach USART-01 RxD.
The [carrier-phase screen](g2/RECEIVER-MASK04-CARRIER-PHASE-SCREEN.md)
finds that 90°/180° rotations preserve 0/12 dibits per stream, while
45°/135° rotations still have at least 2–5 errors per stream after all
375 capture visits are tested. The independent reference receiver decodes
all eight waveforms. Seek an executed carrier-phase adjustment or a
photo-compatible tracking/decision route; keep the fixed Boolean readout
conditional and C3 open.
The [initial-state phase screen](g2/RECEIVER-MASK04-PHASE-SEED-SCREEN.md)
shows that only Q=`5` among four tested seeds reaches the mask-`04`
receiver. With Q=`5`, R5=`40/80/C0` changes captured bytes but does not
decode the 45° input at any of 375 capture visits. Treat Q as an entry
selector under this fixture, and test a live phase-control input or
photo-compatible row-0 latch rather than assuming an initial seed repairs
the fixed decoder.
The [phase-nibble follow-up](g2/RECEIVER-MASK04-LATCHED-NIBBLE-PHASE.md)
also fails to decode the captured Y[3:0] as a fixed-phase differential
symbol across independent streams. Keep the conditional latch experiment,
but seek an executed multi-sample decision or another output source.
The [mask-04 TEST audit](g2/RECEIVER-MASK04-FLAG-CONDITION.md) finds three
surviving previous-flag choices, but none turns the paired ADC difference
into an executed conditional branch. Keep the receive output and mapping
questions open and test another photo-compatible route.
The [mask-04 own-echo replay](g2/JOINT-MASK04-FOUR-ROW-ECHO.md) now joins
its exact executed transmitter samples to the complete four-row receive
loop under labelled echo/ADC assumptions. Neither call nor answer shows
rapid selective attenuation at any remote-responsive direct byte; C4
remains open until a train/freeze route and residual are identified.
The [controller-frame D3EB test](g2/RECEIVER-MASK04-FRAME-MODE-3EB.md)
shows that a labelled `81→A1` mode-byte edge changes several executed
registers but leaves no post-edge history or conditional branch under
this direct input route. Revise the mode lane or output hypothesis and
keep C4 active.
For the next G2 runs, carry the six surviving photo-compatible DAC byte orders
as separate transmitter hypotheses and test their sample/latch timing against
the executed A1–A4 trace. On receive, test a stateful decision/output route
and alternative mode timing with the real PROMs and controller traffic. Record
the visible photo segment, assumed continuation and control fixture for each.
Neither the incomplete DAC trace nor the failed direct `D3EB` mode fixture
blocks these experiments; C2, C3 and C4 remain open until their stated
acceptance evidence is obtained.
The [six-order code comparison](g2/PHOTO-DAC-SURVIVOR-EQUIVALENCE.md) shows
that these orders share every upper-five-bit DAC code on the joined traces;
they differ by at most three counts in the complete 8-bit code. Treat the
low-bit order as an uncertainty to carry through clock/output-route tests,
not as a reason to repeat phase-decision screens or pause for continuity.

The [third-row latch screen](g2/RECEIVER-FOUR-ROW-LATCH-SCREEN.md) samples
every Y-bus bit and ALU flag at `3F8`–`3FA` across seven independent
reference streams. No fixed-phase bit, with either polarity or previous-symbol
XOR, fits even the 36 training dibits exactly. This rejects that simple
output-latch readout under the declared four-row fixture, not the ADC or all
receiver architectures. Continue with a multi-bit/stateful output candidate
or a different photo-compatible mapping; keep G2 active and C3 open.

## Steps

### 1. Check in the field analysis and a static listing

- Add the analysis as a reproducible script: command histogram, must-be-target
  set, window search, subroutine walk, condition-select table.
- Add a new mapping file with the recovered fields and their status.
- Generate a listing of all 1024 words: command, target, condition select,
  17.7, remaining raw bits; plus a control-flow graph with call/loop structure
  and the dispatch tables marked.
- Resolve the 01E outlier (wrong B0/B9 for some words, or a genuine entry into
  a loop body) and re-score.

Done when: every used word is reachable from 000 by fallthrough, branch, call,
return or a marked dispatch table, or is listed as an explained exception.

### 2. Sequencer-only execution

- Drive the existing 8X02 model with the real control flow. Conditions come
  from the scenario: constant, per-select constant, or seeded pseudo-random.
- Model computed dispatch as "call into the table that follows, entry =
  scenario-supplied index". Infer each table's base and entry size from the
  listing.
- Record coverage, stack depth and any stack underflow/overflow against the
  four-entry limit.

Done when: long runs complete with no unknown-stack or bad-address stops, and
random conditions reach most of the store. Stack depth staying within four is
itself a check on the fields.

### 3. Recover the Am2901 fields from the data

Candidate bits are what the sequencer does not use: chip 11 bits 1–7, 17.3,
18.0–18.6, and chip 10 in non-branch words. Constrain them with:

- the register-number counting field above, and any second 4-bit field that
  behaves the same way (A versus B);
- loop setup: a word before each PLP loop must load a count, and something in
  the loop must feed the loop-exit condition;
- 9-bit instruction statistics: destination and source codes in a real program
  are far from uniform (plenty of "no load" and "RAM load", few shifts except
  in multiply/divide style loops such as 1E9);
- chip 10 as an 8-bit immediate (D input) in words where it is not an address,
  read in the same reversed bit order;
- the Am27S31 sine table, the photographed ADC0800 receive candidate, and
  the separate DAC08HP output candidate on DED 3558. The converters are
  identified by marking; their DSP data buses and timing remain untraced.

Score candidate layouts the same way the address field was scored, and keep
alternatives that cannot be separated as named variants.

Done when: one layout, or a short list, decodes every word into a plausible
2901 operation.

### 4. Integrated run

- Sequencer plus two-slice datapath under the recovered mapping. Condition
  selects wired to hypothesised sources (zero, sign, carry, overflow, external
  lines), each switchable from the scenario.
- External world as logged stubs: writes captured with address and value,
  reads supplied by the scenario (constant, table, or the Am27S31 contents).
- Dispatch index taken from the datapath once step 3 suggests which value
  feeds it; scenario-supplied until then.

Done when: the microcode runs for millions of cycles with no model errors and
produces a stable, inspectable trace of register and I/O activity.

### 5. Read the program

- Name the subroutines (multiply loop, table dispatch, filter steps and so on)
  from their traces and annotate the listing.
- Relate I/O activity to the other boards: sine table lookups, DAC writes,
  sample timing, and any exchange with the 8031 controller.
- Feed back into steps 3–4 whenever a routine only makes sense under a
  different field assignment.

### 6. Targeted hardware checks (optional, only where data cannot decide)

A handful of unpowered continuity checks would settle what statistics leave
open, in this order of value:

1. Inputs of the buffer at U4 and whatever else can drive the 8X02 B pins
   (the dispatch source).
2. The condition multiplexer: its select pins against 17.4–17.6 and its eight
   data inputs.
3. Two or three Am2901 instruction pins against chip 11/18 latch outputs, to
   anchor the layout from step 3.

These confirm or correct the model; none of them blocks steps 1–5.
