# Read the program by address

*Runs under the [shared assumptions](ASSUMPTIONS.md).*

Start with [the program overview](PROGRAM-OVERVIEW.md) for the combined
startup, handler, helper and I/O account. The tables below provide the
address-level evidence and the limitations of each interpretation.

The [annotated listing](results/program-reading/listing.csv) consolidates the
current control-flow graph, seven candidate datapath decodes, and evidence-linked
routine interpretations for all 1,024 words. The [catalog](results/program-reading/catalog.json)
records direct-call entries, dispatch targets, unresolved addresses, and source
file hashes. These are generated indexes of existing evidence, not a new
hardware model or a claim that the full program has been understood.

## Reading the columns

- `pc`, `raw`, `command`, `select`, and `direct` give the shared sequencer decode.
  `encoded_target` is the decoded address field even when the instruction does
  not use it as a target. For computed transfers, consult `dispatch` instead.
- `dispatch` preserves the complete scenario table, including repeated indices,
  ROM lookup metadata where present, and its assumption/evidence labels.
- `direct_callers` lists calls that actually use the encoded direct target under
  this scenario. Calls overridden by explicit dispatch tables are excluded.
- Each profile has an `operation` column with its ALU expression, A/B register
  numbers, mapped carry bit and carry-feedback selector. Carry policy remains
  an assumption; these columns do not turn a branch-address byte into a proven
  immediate operand.
- Each profile also has a `labels` column. A name appears only in profiles
  supported by its annotation. `annotations` contains the full meanings,
  profile scopes, limitations, and evidence-document paths relative to this
  directory. Blank labels mean no curated interpretation is supplied.
- `reset_hypothesis_witnesses` links each default-gap word to a replayed
  clean reset trace by witness ID, mapping profile and first cycle. The
  [witness catalog](RESET-WITNESSES.md) preserves all scenario limitations;
  these entries do not merge incompatible mappings into one coverage claim.
- `entry_policy_explanations` records each gap’s witnessed path and the default
  forced jumps that suppress it; the mapping and witness remain explicit.
- `explanation_status` distinguishes reachable code, unresolved entry paths,
  and the three all-FF unused words. A local arithmetic interpretation does
  not change an unresolved entry into an explained exception.

`q1` through `q4` are the [Q-independent candidates](Q-INDEPENDENT.md).
`fitted_original` and `fitted_swapped` are the mappings in the selected
[reset-to-preparation examples](SELECTOR-COMPLETION.md). Their source fields
and register roles differ from the four earlier profiles. The generator
requires all seven profiles to share the sequencer decode before combining them
into one address listing. `joint_mask04` is the later G2 mapping used for the
[same-map transmit/receive run](../g2/JOINT-FOUR-ROW-RETENTION-TX.md). Its
modem-function labels are conditional on the board-route assumptions in the
linked G2 experiments; they do not revise the older profiles.

## G2 modem-function candidates on the joint mask-`04` map

| Addresses | Executed role | What remains assumed |
| --- | --- | --- |
| 127–12A | Candidate DPSK transmit sample loop: controller-derived input sustains the loop and PC 129 selects the upper Am27S31 bank. The raw candidate DAC MSB holds the A1 tone phase, reverses 180° at all 31 A3 boundaries, follows the call/answer A4 dibits, and follows two fresh 32-dibit streams made by ROM-executing the 8031 scrambler on nonzero data. [Training phases](../g2/JOINT-MASK04-MSB-DATA-PHASE.md); [fresh data](../g2/JOINT-MASK04-FRESH-CONTROLLER-PAYLOAD.md) | D127 input rule, one-bit alignment, latch clock, Y7→DAC08 B1 and analog line output; C2 stays open. |
| 3F8–3FE | Candidate ADC-table receive update: the assumed ADC high nibble affects 3F8 Y, 3F9 reads the real ROM at `0x100 + Y`, and the four-row cycle retains input-dependent Q/RAM state. [Trace](../g2/JOINT-MASK04-ADC-ROM-WRAPPER-RULE.md) | ADC ingress, row dispatch and any recovered-bit consumer; C3 stays open. |
| 3EB–3ED | Candidate receive-state byte exposure: 3EB writes R1 from Q's low nibble and 3ED exposes that R1 byte on Y. [Trace](../g2/JOINT-MASK04-ADC-ROM-WRAPPER-RULE.md) | Capture, phase decision and USART RxD/RxC/SYNDET route; C3 stays open. |

The [two-visit selector](../g2/RECEIVER-MASK04-PREAMBLE-TWO-VISIT-SELECTOR.md)
recovers the tested 45° grid streams from these receive-side outputs, but
fails the saved intermediate-angle challenges. It is an external candidate
consumer, not an identified microprogram routine or a verified receiver path.
The separate [cubic transition constraint](../g2/RECEIVER-MASK04-CUBIC-TRANSITION.md)
uses two executed `3F8` visits per symbol and reduces the independent
13-angle readout to one unknown decision in 611, with no wrong decisions.
Its external Boolean relation and USART connection remain unverified.
The [dual-feature consensus](../g2/RECEIVER-MASK04-DUAL-FEATURE-CONSENSUS.md)
combines the two four-bit executed `3F8` captures and recovers all 611
measurable dibits in the held-out 13-angle real-PROM run. The selector,
previous-symbol storage and serial path remain external hypotheses rather
than named microcode instructions.
The [zero-run handoff](../g2/RECEIVER-MASK04-DUAL-ZERO-HANDOFF.md) extends
that same frozen readout to two 64-symbol PROM streams. At 75° and 165° it
recovers the exact eight scrambled zero-run line bytes; the paced USART/8031
model reaches the executed controller `AF→B0` transition only with the
aligned external-sync pulse. Capture and serial wiring remain hypotheses,
so the listing does not label the external consumer as a DSC instruction.
The [random eight-byte handoff](../g2/RECEIVER-MASK04-RANDOM-PAYLOAD-HANDOFF.md)
keeps that frozen readout and recovers four new complete nonzero data
blocks from real-PROM traces, then passes their 32 line octets through
the paced USART and unchanged 8031 descrambler. This strengthens the
candidate receive-loop role, while the external decision logic, frame
edge, bit serializer and physical serial wires remain unverified.
The [new-angle challenge](../g2/RECEIVER-MASK04-RANDOM-ANGLE-CHALLENGE.md)
replays those payloads at 15° and 105° through the unchanged PROM and
frozen readout. It recovers all 252 measurable dibits and 32 line bytes;
the same external route assumptions still limit the interpretation.

## Earlier provisional names

| Addresses | Interpretation | Principal limitation |
| --- | --- | --- |
| 000–012, 054–06E (q3) | Alternative boot entries, fixed-register comparison wait and input-difference tail | Explicit 008 index; longer target bodies and physical completion remain unresolved |
| 013–021 (q3) | Input capture and call-fed external carry wait | Previous flags and explicit early entry; later Q reload selects a separate fixed-register wait |
| 022–031 (q3) | Shift selection and carry-controlled execution of BLT | Zero-Q branch verified locally; skipping BLT retains its actual loop frame |
| 043–044 (q3) | Input difference and clear/capture call before early wait | Alternative selector-3 source; original carry policy bypasses it |
| 1DC–1DE (q3) | Current-flag complement selection between two terminal entries | Current timing and timed early handler-6 diversion; previous timing excludes entry |
| 032–042, 045–04B (q3) | Nested choices selecting the retained comparison input | Declared index sources; 043/044 excluded; timing depends on input carry and zero flags |
| 01C–01F | Call-fed loop entry | Control-flow explanation, not a counted-loop algorithm |
| 06F–077, 112–116 (q3) | Carry-selected half/difference, Q accumulation and register preparation | Local nonzero planes plus zero-reset calls; external channels unknown |
| 04C–053, 09A–09D, 131–132, 228–22A, 238–247 (q3) | Register capture and transient sum/difference sequences | Local actual calls; handler-0 reset waits before reaching these helpers |
| 0E0–0E4 (q3) | Early Q complement and temporary input captures | Timed earlier entry changes the later capture bias and conditional input addition |
| 0CE–0DF, 0E5–0E8 (q3) | Late input capture and masked terminal selection | Timed selector-1 hypothesis; normal and alternative entries retain different R3/R4 |
| 09E–0CD, 0DE (q3) | Masked capture, conditional increment and two Q drains | Diagnostic handler-6 inputs and previous flags; modem purpose unknown |
| 11A–130 (q3) | Fixed-register waits and transient arithmetic sequence | Current flags and BLT replies; temporary Q inputs are overwritten; physical timing unknown |
| 1C3–1CC, 1DA–1DB (q3) | Alternative Q drains and preparation entry | Timed external selector hypotheses; retained-state equivalence does not imply equal output timing |
| 1EF–1FF (q3) | Alternate component construction and two Q drains | New two-selector external-line hypothesis; transient paired output differs from terminal state |
| 1E0–1E8 (q3) | Alternate carry-selected comparison and four computed return leaves | New selector-7 external-source hypothesis; original zero source excludes entry |
| 18B–1C2, 1CD–1D9, 1E7, 3A2–3AA (q3) | Carry-selected comparison, wrapped-sum drain and payload storage | Previous flags, fixed tables and diagnostic replies; bypassed branches excluded |
| 178–17F, 0E9–0EA (q3) | Timed handler-1 continuations and input-parity skip | Previous flags, declared external-line schedule and fixed terminal destination R2 |
| 148–177, 180–186, 2E6–2EB (q3) | Wrapped byte sum with input-dependent shift timing | Handler-1 diagnostic inputs; R14 consumer unknown |
| 259–264, 26A–26F, 2A0–2B2 (q3) | Sum-carry and comparison-selected inputs | Handler-4 code-4 context and fixed dispatch; physical input meaning unknown |
| 230–237, 251–255, 265–269, 0EB–0F9, 280, 28B–28D (q3) | Alternate handler-4 preparation, wrapped input accumulation and direct terminal path | Timed selector-5 input, selector 6 false and global index 3–6 |
| 200–219, 281–286, 28E–295, 2CB–2CE (q3) | Handler-4 replacement or preservation of captured values, nested payload load and indexed stores | Fixed earlier handler inputs and global index 7–15; physical function unresolved |
| 2EC–2FF, 3BB–3BC (q3) | Input preparation and three routes through a common nested return | Local calls, constant selector 1, fixed 21F target 224 |
| 270–27F, 335–340, 357–360 (q3) | Overflow-selected copy, optional captures/complement, and three return sums | Local calls; explicit constant selectors; transient consumers unknown |
| 078–084 | Terminal tail | Physical completion and restart unknown |
| 085–089 | Register right-shift helper; q2 half-Q/input-difference preparation | Not established as serial output |
| 07C–081, 08A–099 (q2) | Two indexed register stores and R0-copy table | Index source and physical output remain unknown |
| 18D, 19C | Successor-byte wait preparation | Tested original-role reset path only |
| 1EC–1EE | External-byte equality poll | Previous-zero condition and external channel remain hypotheses |
| 1E9–1EB | Conditional Q drain | Current versus previous zero flag changes iteration count |
| 341–344 | Preparation with disputed register roles | External operand and destination roles remain hypotheses |
| 370–388 (q3) | Paired self-arithmetic and high-byte wait | Local calls; fixed inputs or preceding-Y dispatch; no physical output assignment |
| 379–388, 392–3A1, 3AB–3BA | Paired add/subtract and permute | Output slots are virtual |
| 3D5–3D9, 3EA–3EE (q2) | Source-overwriting transform loops | Fixed dispatch; nonzero caller states are local fixtures |
| 3C0–3C4 (q2) | Fixed-source transform high-byte loop | Constant dispatch; failed tests repeat without changing source data |
| 3C5–3D4, 3DA–3E9 | Paired quarter-turn transform | Identities were search constraints; nonzero evidence is local |
| 3EF–3FE | Source-overlapping transform | Cannot reuse the independent quarter-turn formula |
| 2BC–2C5 | Nested computed-call wrapper; shifted-Q preparation under q2 | Local nonzero fixtures and Q=0 reset witnesses; scoped dispatch assumptions |
| 221–223, 2B3–2BB (q3) | Temporary input and nested difference call, or Q-preserving comparison return | Outer handler-4 caller, input-derived index and declared selector-5 schedule |
| 224–227, 229–22F (q2) | Nested input-load and Q-exposure leaves | Local 2BC calling context; physical output unknown |
| 2B3–2B8 (q2) | Input-sum capture and carry-qualified return | Prepared R0=Q>>1 forces return; not a global branch constraint |
| 187–18A | Input-matched left shift | Constant nonzero D can prevent return after Q reaches zero |
| 106–107 / 117–118 (q2) | Carry-qualified external waits | Reset R0=FF; zero replies are diagnostic stubs |
| 12C–130 (q2) | Masked external-byte equality poll | Local previous-flag hypothesis; physical input and caller target unknown |
| 126–130 | Idempotent Q-mask tests | No D operand inside helpers; previous/current timing selects different predicates |
| 319–334 | Register-difference scan and carry wait | Shared condition stubs; transient ALU output consumers unknown |
| 300–30A (q3) | Externally gated double preparation and paired wait | Timed diagnostic line; matched reset replies; 1EF excluded only in these contexts |
| 304–308, 311–318 | Double drain and input preparation prefix | Local entry; shared select-5 stub bypasses this path from 300 |
| 30B–310 | Cleared-Q helper (q1–q4) or masked-Q drain (fitted_original) | Different retained R5 values; shared previous-zero and zero-fill hypotheses |
| 345–365 (q3) | Three input-selecting continuations | Zero captured second component; fixed paired/branch indices and separate terminal R2 selection |
| 366–36F (q3) | Overwritten preparation, carry-gated input chain and return Q mask | Constant local reads; one complete ROM zero-reply reset call |
| 36C–36E | Carry-controlled three-add loop | Middle versus last carry depends on flag timing; external operands unknown |
| 100–109, 117–119 (q3) | Startup calls, independent wait/capture bytes and Q-selected handlers | Zero reset, previous flags and declared input schedules; prefixes end before handler execution |
| 109 | Input-code dispatch candidates | Mapping and input schedule change current/previous-Y and Q selectors |
| 002, 076, 109–111 (q1/q3) | Input accumulation, Q-based selector and eight-way handler table | Independent-input prefixes verified; physical command protocol unknown |
| 133–147, 341–344 (q3) | Input-carry and capture-selected transforms | Zero-reset source words and fixed table entry 2; other transform states unresolved |
| 133–13A, 341–344 (q2) | Accumulator carry and threshold gate | Nonzero-Q paths are local fixtures; physical accumulator meaning unresolved |
| 38E–38F (q2) | Preceding-Y paired-arithmetic dispatch candidate | Site-scoped hypothesis; physical index and output consumer unknown |
| 389–391 (q2) | Captured-register copy and paired-arithmetic loop | Final-high-byte exit can return with a nonzero low byte; physical output unknown |
| 28E–295 (q1/q2/q4) | Save R0, optional Q load and byte sum | Select-6 source and physical R15 consumer remain unknown |
| 248–24E | Three-loop shift wrapper | Does not establish R7; each loop has separate input-dependent termination |
| 296–29E | Input-dependent biased Q shift | Most constant-input cases with R7=FF repeat under the selected previous-flag policy |
| 2D0–2D8 | Paired Q drains | Previous-zero policy; transient output meaning unknown |
| 2D8–2DB | Conditional entry into adjustment tail | Requires optional composed BRT gate; default entry remains unresolved |
| 0F9–0FC (fitted_original) | Conditional register-copy tail entry | One gated reset witness; copied value is zero |
| 3BC–3BF | Conditional difference tail | Optional gate; local entry premise; q2 reset entry at index 12, D=01 |
| 2CB–2CF (q2) | Q-zero conditional tail | Optional gate and fixed dispatch; input at 2A8 controls entry |
| 3BC–3BF (q3) | Conditional Q decrement tail | Optional gate; differs from q2 subtraction |
| 287–28A (q3) | Transient Q and register differences | Reset entry demonstrated under q3; output consumer unknown |
| 251–257 (q2) | Zero-sum entry and carry-selected adjustment | Additional three-bit gate; diagnostic input bytes |
| 258 (q2) | Transient difference before preparation re-entry | Optional four-bit gate; output consumer unknown |
| 0FA–0FF (fitted_swapped) | Register copy and Q-zero continuation | Diagnostic alias gate; other graph paths can underflow |
| 2DF–2E5 (q3/q4) | Masked-input continuation test | FF input admits clean reset continuation; other tested bytes can underflow |
| 256–257 | Conditional adjustment selector | Entry from reset and condition meaning unknown |
| 2D9–2DE | Transient one-unit adjustment | No surviving internal effect or identified output consumer |
| 008, 26F, 21F, 2C4 | ROM-backed dispatch candidates | Site/bank/range/index associations remain hypotheses |

These annotations cover 1021 used words, including overlaps and disconnected
local probes. That count is not a measure of understood modem functionality.
The catalog additionally lists direct-call entry points with linear-walk
boundary hints; a linear walk is not a complete routine control-flow analysis.
Every used word now has a scoped annotation. The [overview](PROGRAM-OVERVIEW.md)
and [final review](FINAL-REVIEW.md) complete the program reading and acceptance
audit; annotations across profiles are not combined into a physical-machine claim.

## Coverage stays separated

| Listing column | Evidence | Used words |
| --- | --- | --- |
| `static_reachable` | Combined local-case graph | 999 |
| `sequencer_sweep_visited` | Its fixed 128-seed sequencer sweep | 941 |
| `reset_original_visited` | Selected fitted original-role reset example | 187 |
| `reset_swapped_visited` | Selected fitted swapped-role reset example | 186 |
| `reset_q2_nested_visited` | Q2 seed-115 reset example entering the nested ROM wrapper | 187 |

The selected reset examples use different datapath/condition hypotheses from the
sequencer sweep. These columns are not merged into a single execution claim.
For example, 2D9 has both a local interpretation and a clean reset witness
under an optional gate, but remains outside the default graph. All 22 default
gaps now have replay-verified witnesses in five runs across three mappings.
Their states, artifact paths and conservative graph exceptions are embedded
in the catalog; default reachability and interpretation labels stay separate.

## Reproduce

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/joint_mask04_program_profile.py
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/program_reading.py \
  --out /tmp/nokia-program-reading
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -p 'test_*.py'
```

[Annotation manifest](program-reading.json) owns every curated label and its
scope. The generator validates evidence paths, profile names, address ranges,
shared control decode, and consistency of the saved sweep with a freshly
computed graph. It also replays the five gap witnesses and rejects missing,
failed, truncated or altered evidence. Both output files reproduce byte for
byte. The functional/assumption tests include checks that
interpretation labels do not leak across profiles or hide default unresolved
entries. The [final review](FINAL-REVIEW.md) records completion within the plan's
assumption-driven scope.
Physical I/O routing remains an explicitly labelled hypothesis.

The later [q2 tail-exclusion argument](TAIL-EXCLUSION.md) explains the absence
of 287–28A under the optional gate and zero-reset scenario. It checks every
entry and the reaching register writes, allowing arbitrary external bytes and
declared dispatch entries. This scoped explanation does not change the default
listing's unresolved hardware-entry labels.

The [diagnostic register-store contract](REGISTER-CONTRACT.md) connects the
nested Q load to the terminal stores using explicitly constructed input bytes.
It exhausts destination pairs from a verified reset checkpoint, preserves
register side effects, and does not identify a physical controller protocol.

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

[The plan acceptance audit](PLAN-AUDIT.md) verifies the current long-run and
coverage evidence separately from interpretation. All 37 cataloged direct-call
entries and all used words have scoped annotations; the program overview and
final requirement review complete the interpretation work. Physical fidelity is not added as a prerequisite
beyond the plan’s explicit assumption-based scope.

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

[Handler 4's bank-200 continuations](HANDLER4-BANK.md) connect all nine
remaining high table indices to input replacement or capture preservation.
Real nested calls return through 2FF, payload-zero changes the short-path
terminal skip, and indexed stores can overwrite the retained R12/R14/R15.

[Handler 4's alternate preparation and additive routes](HANDLER4-ALTERNATIVES.md)
connect a timed selector-5 fall to preserved input Q, carry-derived R14 and
four terminal destinations. The 230/0ED path performs two wrapped additions;
280 stores directly, and zero payload shortens either path by one instruction.

[Handler 1's parity and timed continuations](HANDLER1-BRANCHES.md) connect
D164 parity to Q, the previous-OR skip at 17F, and final R5=0/127. Different
external-line schedules have equal final state with a checked timing difference;
late-transition controls distinguish the two branch sampling cycles.

[Handler 2's alternate preparation and return leaves](HANDLER2-ALTERNATE.md)
separate the original entry exclusion from a declared external-line hypothesis.
The carry-selected comparison survives in R12; four preceding-Y-selected POP
leaves expose distinct temporary R3 values but share the final payload result.

[The complete startup contract](STARTUP-CONTRACT.md) connects preparation
calls, two external waits and Q-selected dispatch for all byte codes. Independent
capture reads determine R6/R7 while PLP-side replies control release; held
replies prove period-two recurrence. The second R4 capture replaces the first.

[Outer input and comparison-return leaves](INPUT-LEAVES.md) connect all
nineteen selecting input bytes to real calls of 221 or 2B3. They distinguish
temporary replacement from Q preservation and explain why this caller takes
2B9–2BB while the earlier nested wrapper takes 227.

[The final two branch blocks](FINAL-BLOCKS.md) connect the early clear/capture
call and current-flag complement exit to full reset contracts. The listing now
has scoped annotations for every used word; source and timing exclusions remain
explicit; the program overview and final acceptance review complete the plan.
