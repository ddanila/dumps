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
| 3F8–3FE | Candidate ADC-table receive update: the assumed ADC high nibble affects 3F8 Y, 3F9 reads the real ROM at `0x100 + Y`, and the four-row cycle computes input-dependent Q/RAM state. A one-sample impulse changes the tested state only while that sample is held. [Arithmetic](../g2/JOINT-MASK04-ADC-ROM-WRAPPER-RULE.md); [impulse](../g2/JOINT-MASK04-RECEIVE-IMPULSE-MEMORY.md) | ADC ingress, row dispatch, mode/feedback path and any recovered-bit consumer; C3 stays open. |
| 3EB–3ED | Candidate receive-state byte exposure: 3EB writes R1 from Q's low nibble and 3ED exposes that R1 byte on Y. [Trace](../g2/JOINT-MASK04-ADC-ROM-WRAPPER-RULE.md) | Capture, phase decision and USART RxD/RxC/SYNDET route; C3 stays open. |

The [full-byte `12A` phase replay](../g2/JOINT-MASK04-12A-FULL-BUS-PHASE.md)
strengthens the transmit label under the joint map. In both unchanged
controller-fed streams, all six photo-compatible candidate DAC bytes show
a 2,100 Hz tone peak and 31 exact 180° segment-1 reversals. The 32 data
steps per mode/bus fall within the intended quadrants only after the
previously fixed Q=0.5 line filter and matched symbol window; raw
eight-sample phasors are less accurate. This is a conditional signal
signature of executed Y bytes, not a traced DAC08 input or line current.

The [full-byte sampled-byte audit](../g2/JOINT-MASK04-FULL-BUS-ADC-ROW-IDENTITY.md)
qualifies these receive names. At all 3,900 captured `3F8` visits in six
real-PROM streams, Y equals the modeled ADC high nibble with low bits `F`.
At three sample boundaries per symbol, the observed `3ED` row-0 byte is a
codebook of the preceding ADC high nibble, and row-3 is a codebook of the
current one. These outputs expose quantized input samples; a dibit decoded
externally from them is not yet an executed microprogram decision. The
`3F9` ROM read and retained Q/RAM updates still merit a downstream-output
test before naming a receive-demodulation routine or passing C3.
The later [20-state row-phase rule](../g2/JOINT-MASK04-12A-ROW0-TWENTY-STATE.md)
uses executed `3ED` row-0 bit 0 and two `3F8` Y snapshots to recover all
64 measurable receive decisions in each of six fresh Tx→line→Rx runs at
75–125% level. At aligned modeled USART timing the eight line bytes and
eight 8031-decoded source bytes are exact. The
[cycle replay](../g2/JOINT-MASK04-12A-ROW0-SERIAL-TIMING.md) places the
second snapshot 2,961 microcycles before the proposed first RxC sample.
Two new [four-row real-PROM captures](../g2/JOINT-MASK04-12A-ALL-ROW-LATCH.md)
show why an unqualified output latch cannot implement this rule: rows 1
and 2 are zero at all 520 checked symbol/visit points, while a latch
clocked after every `3ED` would finish on row 3 and make 14/64 call or
19/64 answer decision errors. The separate raw-PROM
[U19 clock candidate](../g2/RECEIVER-MASK04-3ED-PROM-LATCH.md) fires after
every row; since the same `3ED` word is executed four times, its PROM
decode cannot by itself select row 0. A row index from the photographed
U24 counter or another stateful qualifier could do that, but its wiring,
reset phase and the required extra storage are untraced. These phase gates
and serial decisions are external readout hypotheses, not executed DSC
instructions or a physical C3 pass.
The original 20-state gate failed at a new carrier start because it
assigned previously unseen state `5E` the wrong phase. After moving
that fixture into development, a revised
[22-state rule](../g2/JOINT-MASK04-12A-ROW0-TWENTYTWO-HOLDOUT.md)
recovered fresh payloads at that start. A subsequent frozen
[phase-120 holdout](../g2/JOINT-MASK04-12A-ROW0-PHASE120.md) reached
another unseen state, `59`, on 40 call and 42 answer symbols; both
executed PROM streams and the modeled 8251/8031 handoff recovered
exact bytes, and the new state's phase prediction had zero graph
conflicts. This validates a limited external consumer transfer, while
the searched `3F8`/`3ED` bytes still show sample encoding rather than
an identified microprogram bit decision.
The [three-phase `3F9`/`3FA` capture](../g2/JOINT-MASK04-RECEIVE-3F9-3FA-CODEBOOK.md)
now tests their executed Y bytes at all 9,000 visits of three legal
rotated-carrier streams. Both execute once per ADC visit, and each Y byte
is single-valued by the current ADC high nibble across all sixteen codes
and 110 observed adjacent-sample pairs. `3F9` has 15 output values;
`3FA` has only `20`/`21`. This observed route is an input-sample
recoding, not evidence that either word emits a received bit. The
transient Q/RAM, external feedback and downstream physical route remain
open C3 candidates.
The [full 32-word history scan](../g2/JOINT-MASK04-RECEIVE-HISTORY-SCAN.md)
checks all Y, Q and RAM sites in five legal rotated-payload streams.
After current ADC selection, Y/Q at every word are single-valued by
that current high nibble. R12/R13 still vary with the previous high
nibble at `3F8`, R13 at `3F9`, and no RAM byte varies with it from
`3FA` onward. This aligns the prior pulse trace's carryover with the
**preselection** prefix and narrows any direct-mode C3 consumer to
that window or a different mode/feedback path.
The [matched-tail impulse test](../g2/JOINT-MASK04-RECEIVE-IMPULSE-MEMORY.md)
adds a time limit to that statement: under the tested four-row `D3EB=01`
fixture, one changed ADC high nibble affects Q/RAM and intermediate Y
at the selected capture points only during its held sample. The first
identical-input ADC visit after the pulse has no captured difference,
on either a constant or varying waveform. The
[full-word differential trace](../g2/JOINT-MASK04-RECEIVE-PULSE-CARRYOVER.md)
finds a shorter history window that the captures missed: 21 executed
words before the next `3F8` read still differ in Y, Q, register writes
or ROM reads; the whole state rejoins at the next `3FA` word. This is
previous-sample carryover, not a retained symbol decision.
The [raw-PROM U19/U12 replay](../g2/JOINT-MASK04-CARRYOVER-LATCH-PULSE.md)
then shows a conditional external memory of that transient: a row-0-only
`3ED` edge captures the previous-sample low nibble, and a modeled U12
still holds it at row 3 after the DSC state rejoins. At the first
restored-input visit, held `0/5` accompanies identical live row-3
Y[2:0]=`2`. The unqualified every-row clock instead overwrites the
value with zero. The gate and U12 data/consumer wires remain assumed;
the earlier 45° decoder failure keeps this from being a C3 decision.
Holding the controller's observed `81` or `A1` frame byte at the
[candidate `3EB` D input](../g2/JOINT-MASK04-RECEIVE-MODE-IMPULSE.md)
also leaves no post-pulse captured difference on the varying waveform.
That constrains the direct frame-byte lane, not an untraced external
RAM return or a different mode gate.
The [delayed RAM-return trace](../g2/JOINT-MASK04-RAM-RETURN-ARITHMETIC.md)
now resolves `3FA` more precisely under one assumed external return.
Its executed low/high Am2901 instructions are `55/C5`: the low nibble
forms `Dlo + ~R10lo + carry`, while the high nibble forms
`Dhi + R10hi + low_carry`. Only R13's high nibble is written. A stored
`01→0F` byte changes Y `20→2E` or `30→3E` for the delayed read, but
matched baseline/pulse cycles leave Q and the written R13 identical.
The generated `joint_mask04_operation` listing describes the low-slice
operation; it must not be read as a full-byte subtraction or an
identified echo residual. The RAM wiring and Y consumer remain open.
The [high-nibble `3FA` return control](../g2/JOINT-MASK04-RAM-HIGH-RETURN-EXIT.md)
puts `3F9` or `3FA` Y's high nibble into a sample-paced hypothetical
external RAM and returns it at `3FA` under a previous-overflow TEST
assumption. Unlike write-only or read-only
controls, both feedback variants leave the four-row loop at `3ED→3EE`
before the offered sample-25 pulse. Their post-exit traces take 53
transition words and then remain in `1E9/1EA` for the rest of the run,
without another ADC selection. This is an executed control-flow
effect of the assumed return, not evidence of useful echo adaptation.
The [TEST-source challenge](../g2/JOINT-MASK04-RAM-CONDITION-RESCUE.md)
changes that result: previous carry sustains the same `3F9`-latched
high return for 3,000 ADC visits. It also sustains the subsequent
[own/remote/mixed run](../g2/JOINT-MASK04-RAM-CARRY-ECHO-SCREEN.md),
but `3FA` code-space differences grow late rather than selectively
falling for the own echo. The condition mux and RAM return remain
untraced; this is an active but non-cancelling candidate, not C4.
The [24,000-word arithmetic audit](../g2/JOINT-MASK04-RAM-CARRY-ARITHMETIC.md)
finds R10=`10` at every `3FA` operand read across the four training
inputs, even though R10 changes elsewhere in the loop. With the
assumed RAM D low nibble forced to `1`, this site's executed output
reduces to `Yhi=(Dhi+2)&15`, `Ylo=carry_in`. That is a delayed input
code plus current carry at this proposed output site, not a varying
trained R10 estimate.
The [paired full-word propagation trace](../g2/JOINT-MASK04-RAM-CARRY-PROPAGATION.md)
shows where this candidate return's effect ends. Against a same-input
write-only control, it changes only `3FA` Y and R13 writes on the
64-sample varying and 192-sample mixed own-echo/remote streams. Every
changed R13 value is overwritten six cycles later at `3FC`; later ALU
words, Q, TEST and PC path agree. An external latch might still capture
`3FA` Y, but this tested internal route supplies no retained estimate
to a later executed operand. Its physical wires and line effect remain
unverified.
The [sample-paced latch screen](../g2/JOINT-MASK04-RAM-CARRY-LATCH-PHASE.md)
shows that `3FA` Y itself is constant over each held ADC sample on all
four inputs with and without high RAM return. Every one of 46 candidate
fixed latch phases therefore captures the same per-sample code; none
turns this tested code-space echo response into selective attenuation.
Moving the same hypothetical return to the other stub D site, `3FC`,
has a [different executed effect](../g2/JOINT-MASK04-RAM-CARRY-3FC-PROPAGATION.md):
its changed Y changes the `3FD` ROM address/read and ALU Y on both a
64-sample varying and a 192-sample mixed stream. R10/R13 change briefly,
but Q, TEST, PC path and all ALU sites after `3FD` agree with write-only
controls. This is a candidate delayed-input transform, still lacking a
line-output connection or selective echo-residual test.
The [eight-run `3FD` echo challenge](../g2/JOINT-MASK04-RAM-CARRY-3FD-ECHO-SCREEN.md)
then finds that this output is constant across own, remote, mixed and zero
inputs without RAM readback. Readback makes it input-sensitive, but both
own-echo-versus-zero and mixed-versus-remote Y-byte contrasts grow between
early and late training. All 46 candidate sample-paced latch phases agree,
and only three tail samples retain the frozen RAM effect. This supports a
delayed-input lookup under the stated mux, not a demonstrated echo canceler.
The [split-slice audit](../g2/JOINT-MASK04-RAM-CARRY-3FC-ARITHMETIC.md)
checks every training `3FC`/`3FD` pair across all four inputs. It finds
R10=`10`, carry=0 at `3FC`, giving `Y=(RAM_D+0x10)&0xff`, followed by
real-ROM address `0x100+Y`. At `3FD`, R5=`00`, carry=1, and Y is the
ROM byte's high nibble plus one, shifted into the high output nibble.
That explains the changed `3FD` code without an adaptive operand at
either tested word.

The [executed phase-accumulator check](../g2/JOINT-MASK04-TX-PHASE-ACCUMULATOR.md)
gives `127–12A` a specific candidate modem function: R1 adds the D127
step modulo 256 at each visit, and Y7 exposes its high bit throughout
the loop. In the labelled controller-to-D127 pulse fixture, `88` and
`B0` yield the 2,100 Hz and magnitude-1,800 Hz phase steps at the
assumed 9,600 Hz sample clock; four-visit dibit pulses shift the phase
by quadrants. The physical output route remains unverified.
The [full-A4 intervention](../g2/JOINT-MASK04-TX-PHASE-PULSE-ABLATION.md)
then verifies those R1 and Y7 relations across all 32 real-controller
data dibits per selector. Replacing dibit 23's four `90` D127 visits
with `B0` leaves prior symbol phases unchanged and offsets all later
symbol ends by 128/256 in both modes. That directly ties one offered
controller dibit pulse to persistent executed carrier phase under the
assumed input route, without identifying its physical DAC output.
The [buffered TxD-bit intervention](../g2/JOINT-MASK04-BUFFERED-TXD-BIT-ABLATION.md)
then starts one step earlier in that assumed route: it flips an actual
8031/8251 TxD stream bit in a controlled counterfactual, buffers the
completed pair to the next symbol boundary, and changes four D127
visits. Both full real-PROM mutant streams match the R1/Y7 recurrence
at all 846 output samples, with no Y7 change before the buffered pulse.
This constrains the causal digital path while leaving the external
pair latch, gate and DAC line physically unidentified.
The [full controller-fed bank-phase replay](../g2/JOINT-MASK04-TX-BANK-PHASE.md)
adds a separate `12A` result: changing only Am27S31 A8 at `129`
changes `12A` Y bit 0 on about 75,000 raw visits per selector and on
198/202 of 832 phase-0 candidate DAC samples. The six surviving bus
orders map that bit to a 16-count code step. Both bank choices retain
the 2,100 Hz tone and zero filtered A3/A4 data errors in this fixture;
the `129` Y site remains unchanged. This narrows where ROM data could
reach a DAC latch without verifying that physical connection.
The [U10 D2 edge comparison](../g2/JOINT-MASK04-TX-BANK-EDGE-TIMING.md)
adds the timing condition: the raw PROM bit rises at `129` and falls at
`12A`, but preceding-word Y at both edges is bank-insensitive. The
bank-dependent `12A` Y must settle before any candidate DAC latch
captures it. No clock/data propagation order is established by the photos.
The [two-stage hold replay](../g2/JOINT-MASK04-TX-12A-TWO-STAGE-LATCH.md)
models the photographed 74LS373 as transparent during `12A`, closing at
`12A→127`, and the nearby 74LS273 as clocked later by a possible
`127→128` PROM decode. Across call/answer and both selected ROM banks,
the held route preserves 198/202 bank-sensitive samples while a
transparent-through-`127` control preserves none. This is a more explicit
conditional output-timing route; neither chip's data/clock nets nor the
DAC08 input byte has been identified electrically.
The [parallel-latch replay](../g2/JOINT-MASK04-TX-PARALLEL-LATCH-BUS.md)
tests a route closer to the visible four D–D and four Q–Q latch-track
pairings: the 74LS273 directly captures settled `12A` Y at an assumed
early clock. It reproduces the same candidate bytes, but an enabled
transparent 74LS373 would drive opposite values on the tied Q lines
before every checked clock. Its output enable must arbitrate that bus
under this model; the actual control net remains unknown.
The [integrated event replay](../g2/JOINT-MASK04-TX-PARALLEL-CLOCK-SCHEDULE.md)
then applies a unique raw-PROM `12A` decode and assumed 375-edge counter
to both full controller-fed executions. It selects 832 clocks exactly
1,500 PROM cycles apart, capturing the same settled-`12A` bytes while a
late-edge control captures a different stream. This gives the candidate
transmit sample loop an explicit executable clock path, conditional on
the 74LS273 setup/hold order, 74LS373 output enable and DAC/line nets.
The [photo-B5 alternative](../g2/JOINT-MASK04-PHOTO-B5-Y7-ROUTE.md)
projects those same executed Y7 samples through an assumed LS273 D4
input and the photo-suggested Q4→DAC08 B5 segment. It preserves the
conditional tone and dibit behavior, but does not establish whether
the actual DAC assignment is B5, B1 or another route.

The [transmit ROM-bank ablation](../g2/JOINT-MASK04-TX-ROM-BANK-ABLATION.md)
qualifies the `127–12A` interpretation: switching the selected `129`
operand bank changes the executed trace but not one of the captured
candidate Y samples in either full controller stream. The upper-bank
choice is therefore not evidence that those ROM bytes generate the
carrier in this fixture. `12E` has zero visits in these streams.
The [first-difference trace](../g2/JOINT-MASK04-TX-ROM-IMPACT.md)
confirms that each selected `129` byte changes, affects ALU `f` and
temporary register writes, and sometimes changes `12A` Y lower bits.
Y7 remains equal throughout the tested tone window. This preserves
the distinction between active ROM arithmetic and the proposed output
bit's insensitivity to that bank change.
The [split-slice ROM-carry audit](../g2/JOINT-MASK04-TX-ROM-CARRY-EQUATION.md)
identifies the path through `129–12A`: low/high `C9/8D` at `129`
use R1, R0 and the selected ROM byte; the high-slice carry then enters
low/high `C1/85` at `12A`. There, low Y is R1lo+R0lo+that carry
modulo 16 while high Y exposes R1hi. Every paired-bank Y0 change in
the short tone and data-prefix runs coincides with a changed carry.
This gives the candidate ROM-sensitive output byte an executed
arithmetic explanation, still conditional on the selected bank and
an external `12A` latch route.

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
The [±7 Hz payload handoff](../g2/RECEIVER-MASK04-OFFSET-PAYLOAD-HANDOFF.md)
also recovers two fresh scrambled payloads through the frozen
ADC-margin readout and the paced 8251/8031 model. Its capture selector
and physical serial route remain external hypotheses, so C3 is open.

The later [thirteen-bit staged capture](../g2/JOINT-MASK04-12A-MODEBIT156-STAGED-TRANSFER.md)
gives this candidate receiver a more explicit timed readout. Two
executed `3F8` Y visits, a late row-0 Y bit, visit-141 Y6 and an
assumed `3EB` mode bit are held through a proposed U14→U3 transfer and
U25 capture before an assumed U28 phase/dibit load. The staged replay
matches all 7,020 saved thirteen-bit states. A revised eight/five-product
phase witness fits a connected, conflict-free 159-state graph. With that
witness frozen, four fresh 1.15× streams and four fresh 0.85× streams
recover exact modeled line and executed-controller bytes. The lower-gain
later-edge call reaches one previously unseen state, `1909`; its two
neighboring known states require phase 2, which the frozen witness
predicts. This is a runnable account of a possible external decision
and serial path from executed DSC sample codes. The physical gate,
capture/clock nets, ADC/line route and USART connections remain assumed,
so the microprogram itself is still identified as producing the sample
state, not as executing the final dibit decision.

The [one-run conditional modem demonstration](../g2/JOINT-MASK04-END-TO-END-DEMO.md)
joins these candidate functions. Eight locally ROM-scrambled 8031 bytes
drive the buffered `127–12A` loop; 846 executed `12A` samples form a
modeled DAC/line waveform with a 2,100 Hz A1 tone. Feeding its quantized
samples to the executed `3F8–3FE` loop and the frozen external
thirteen-bit capture/phase/USART route recovers all eight original
controller bytes with zero modeled decision errors. The short
random-data spectrum peaks at 1,650 Hz, not an established stationary
1,800 Hz line peak; a separate
[constant-B0 PROM control](../g2/JOINT-MASK04-STATIONARY-CARRIER-CONTROL.md)
places all six candidate DAC orders at 1,800 Hz. The DAC/ADC/analog and
serial nets remain assumed;
this run shows a coherent possible modem function of the microprogram,
not a physical board-level acceptance pass.

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
