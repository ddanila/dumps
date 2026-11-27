# DSC2847 microcode emulation plan

> **Status:** G1 complete ([final review](assumed/FINAL-REVIEW.md)); **G2 active**
> in [PLAN-2.md](PLAN-2.md#goal-g2). Ambiguous photographed connections are
> testable assumptions, not G2 blockers. Run photo-compatible hypotheses with
> the available dumps and keep physical confirmation as a separate acceptance
> question.

## Treat uncertain connections as runnable hypotheses

Use the existing photographs to build the simplest pin-compatible route for
each missing DAC, ADC, latch, clock, DSC-to-USART or analog-line connection.
Record what is visible separately from each assumed net, polarity, enable and
clock/latch phase. Run the real-ROM/controller stimulus under that assumption,
with a control that changes the disputed connection or timing. Record the
observation that would favor or reject the route and the next runnable candidate.

A failed run rejects only its stated wiring, timing and input fixture. Try the
next photo-compatible route, changed stimulus or independent microcode/signal
test; continue other open checks while revising that route. Do not wait for new
photos, continuity checks or user confirmation before running an explicit
assumption. Keep G2 **active** and C2/C3/C4 **open** while experiments remain
possible. Record missing physical continuity as an open validation question,
not a stop condition for simulation. A plausible execution is conditional
evidence, not proof of the physical circuit or an automatic acceptance pass.
Consider a goal-level blocker only after documenting why no remaining runnable
experiment can advance an open check and what specific external observation is
required.

**Current blocker decision:** G2 is active. The disputed DED latch tracks and
the receiver's mode, clock and serial-input nets are reasons to run explicit
photo-compatible models, not reasons to pause. For C2, test a direct 74LS273
capture at `12A` against the later-edge alternative, including the required
setup/hold timing. For C3, treat the `3EB` mode-bit capture and its phase and
serializer wiring as stated assumptions; freeze a candidate decoder before
testing fresh controller-fed, real-PROM streams. If a candidate fails, record
the failed fixture and try another pin-compatible route or an independent
signal constraint. Keep C2/C3 open until their acceptance evidence is met;
neither a plausible simulation nor an untraced wire settles them.

When a proposed route needs a photographed part already assigned another
*assumed* role, test the competing allocations separately. For example, using
both U25 flip-flops for late receive captures leaves the earlier candidate's
previous-phase memory unallocated. That is a concrete circuit-design question:
replay the capture timing, then seek a photo-compatible phase/serializer path
or another allocation. It does not stop G2 merely because the first combined
allocation is incomplete. Keep the missing capacity, nets and timing visible
in the result, and reserve C3 acceptance for an executed, constrained route.

Apply this rule to each open check: name the photo-supported candidate and its
uncertain nets; run a real-ROM/controller fixture with a discriminating control;
record what passed or failed under that assumption; then choose the next
candidate. If the available photographs support several routes, keep them as
separate variants and test them in turn. Exhaustion of one route, a missing
continuity measurement, or an unconfirmed physical net does **not** by itself
block G2. Only report a blocker after the runnable variants and independent
tests have been exhausted, with the missing observation stated precisely.

For C2, test the candidate Y7-to-latch-to-DAC08 MSB and analog-output route
identified by the [MSB-only replay](g2/JOINT-MASK04-DAC-MSB-DATA.md).
The [PC129 ROM-bank ablation](g2/JOINT-MASK04-TX-ROM-BANK-ABLATION.md)
now changes only Am27S31 A8 at `129` in both full controller-fed A1–A4
runs. Their internal trace digests change, but their candidate Y sample
hashes and all tone/data scores are identical at the `129` sample phase.
Do not treat upper-bank `129` selection as evidence for carrier synthesis
on that route. Test where `129` first affects retained state or a
different output phase while
keeping the DAC line path open. The separate `12E` bank control makes no
difference because `12E` is never visited in these sustained streams.
The [first-difference trace](g2/JOINT-MASK04-TX-ROM-IMPACT.md) shows
1,014 changed selected `129` ROM bytes in 4,096 executed tone-loop
cycles. They change ALU `f` and register writes, plus 221 transient
`12A` Y lower bytes; Y7, Q and PC path remain equal. Do not describe
the ROM as ignored. Seek the actual latch source or a mode where the
changed internal state reaches a measured output.
The [split-slice ROM-carry audit](g2/JOINT-MASK04-TX-ROM-CARRY-EQUATION.md)
now explains the ROM-sensitive `12A` Y0 path. For each reached `129`
and `12A`, checked `C9/8D` and `C1/85` instructions put the selected
ROM high nibble into `129`'s high-slice carry, then add that carry
to R1lo and R0lo at `12A`. Upper-versus-lower bank changes this
carry on 221/1,014 tone visits and 254/1,014 data-prefix visits;
exactly those `12A` Y bytes change, always by XOR `01`, while R1
and entering R0lo agree. This is executed arithmetic evidence for a
ROM-dependent candidate DAC byte, conditional on the bank select and
post-`12A` capture route. Keep C2/G2 active.
For C3, the [photo-latch capacity replay](g2/JOINT-MASK04-12A-ROW0-PHOTO-LATCHES.md)
tests an explicit U12/U14/U3 seven-bit capture route against eight saved
real-PROM receive streams. The aligned, frozen 22-state gate replays exact
modeled USART and executed controller bytes in every run; changed row/Y
captures and an early RxC provide discriminating controls. This is a
conditional circuit capacity and timing result, not identified wiring or a
C3 pass. Next test raw row-clock qualification on a fresh all-row PROM
capture while keeping the latch/serial nets assumed and G2 active.
The [phase-112 all-row execution](g2/JOINT-MASK04-12A-ALL-ROW-PHASE112.md)
now performs that changed-carrier test with the frozen 22-state gates:
both mode traces match saved real-PROM hashes, row-0 qualification is exact,
and an unqualified every-row clock leaves row 3 with 19/64 and 15/64
errors. This narrows the required logical clock selection, not the actual
U24/U12 nets. Test a photo-compatible raw-PROM gate timing next.
The [two-edge PROM replay](g2/JOINT-MASK04-12A-ROW-CLOCK-TWO-EDGE.md)
now finds separate raw-decode edges at `3ED→3EA` for candidate row
capture and `3EA→3EB` for counter advance on both full phase-112
receive runs. A seeded modulo-four qualifier retains every fourth row
without logical phase drift, and the checked values agree with the
earlier all-row capture. U24 reset phase, actual gate wiring and
electrical timing are still assumptions. Test counter initialization
under a natural mode transition; keep C3/G2 active.
The [full mode-edge phase holdout](g2/JOINT-MASK04-12A-MODE-PHASE-HOLDOUT.md)
tests that transition through the real-PROM receiver with an assumed
controller `81→A1` input at `3EB`. The PC path and two-edge row clock
survive, but the old `01`-trained phase gate fails. A gate frozen on the
call-side changed-mode states recovers exact dibits, line bytes and
modeled USART/executed controller payloads on answer-side held-`81`
and edge mode-condition holdouts. Their bytes appeared in earlier
`01`-mode development, but the changed-mode executions did not. State
`09` requires different labels across
the earlier `01` and new `81` development graphs; a conditional mode
selector is therefore required for this seven-bit readout. Its physical
source and the serial path are still assumptions. Challenge fresh
mode/phase data; keep C3/G2 active.
The [fresh changed-mode phase-120 challenge](g2/JOINT-MASK04-12A-MODE-TWELVE-HOLDOUT.md)
rejects the eight-state gate on two new payloads: 9/64 and 12/64
wrong dibits, all involving new state `36`. The anchored transition
graph remains conflict-free and assigns `36` phase 0, while the frozen
gate assigned 1. A 12-state revision frozen after that failure then
recovers exact dibits, line bytes and modeled USART/executed controller
payloads on a separate new pair. The answer-side reference decoder
misses two dibits, and the holdout adds no unseen states. Keep the
external logic, mode route and serial nets conditional; test another
phase/gain fixture and keep C3/G2 active.
The [phase-128 changed-mode holdout](g2/JOINT-MASK04-12A-MODE-PHASE128.md)
keeps those 12-state gates frozen on two more controller-fed payloads
and a new R1 carrier start. Both full real-PROM receiver runs recover
all 64 dibits, exact line bytes and exact modeled USART/executed
controller source bytes. They use only known states, including
mode-sensitive `09`, so they validate this carrier transfer without
resolving unobserved states or the physical mode/serial route. Keep
C3/G2 active and challenge a distinct state family next.
The [U15 phase-gate capacity audit](g2/PHOTO-U15-PHASE-GATE-CAPACITY.md)
corrects the photographed S64 package to 14 pins and exhausts its
fixed 4-2-3-2 AOI structure against 34 observed mode-conditioned
phase labels. It can express one combined phase bit, but not the other
in either output polarity from direct state-plus-mode inputs. A
photo-compatible multistage gate path remains to test; the physical
phase/USART nets and C3/G2 remain open.
The [U13/U15/U19/U21 candidate circuit](g2/PHOTO-U15-U19-U21-PHASE-ROUTE.md)
uses the photographed package gate budgets to implement both observed
mode-conditioned phase outputs. It reproduces all 34 fitted labels and
0/640 dibit errors across ten saved real-PROM receive streams. Those
streams contain no unseen states, and the gate nets remain assumed;
freeze this circuit for a new carrier/gain fixture and keep C3/G2 open.
The [phase-125 unseen-state challenge](g2/JOINT-MASK04-12A-MODE-PHASE125-CIRCUIT.md)
now freezes that circuit on two new full real-PROM call/answer runs.
Both visit new state `3D`, whose phase is independently constrained to
1 by 14 and 8 adjacent transitions. The prior cover predicts 0 and
misses 14/64 and 8/64 dibits; the package circuit predicts 1 and
recovers 0/64 errors plus exact modeled serial/executed controller
bytes in both runs. This tests one new state under assumed wiring;
challenge another gain/clock fixture and keep C3/G2 open.
The [matched phase-131 gain challenge](g2/JOINT-MASK04-12A-MODE-PHASE131-GAIN.md)
now supplies that changed-gain control. At original gain, new state
`4C` has phase 1 from 18 neighboring constraints and the frozen
package circuit makes 0/64 errors in both call/answer runs. At 1.25×
gain with identical transmitter bytes and PC path, the receive state
alphabet switches to four new states; their relative phase graph has
zero conflicts, but the frozen circuit misses 16/64 and 10/64 dibits
and delivers wrong controller bytes. This rejects that fixed gate
under the boosted-gain assumption. Sweep the gain transition and test
another capture bit/timing route; keep C3/G2 active.
The [phase-131 gain sweep](g2/JOINT-MASK04-12A-MODE-PHASE131-GAIN-SWEEP.md)
reconstructs the matched ADC waveform and executes intermediate
real-PROM receive runs. The frozen circuit remains exact at 1.125×,
then fails 12/64 call and 11/64 answer at 1.150× with **zero** clipped
PCM samples. Across the sweep, the new-state phase graph has no
conflicts; only `48` and `2F` disagree with the frozen circuit, both
on phase bit 0, and every wrong transition crosses one of them.
This localizes the next test to an alternate capture bit/edge or
multistage phase-bit-0 path under the same line input; C3/G2 stay open.
The [capture-wire and adjacent-visit controls](g2/JOINT-MASK04-12A-PHASE131-CAPTURE-CONTROLS.md)
now screen 448 one-bit substitutions on 22 saved real-PROM cases.
All 137 changes preserving zero errors on 16 prior cases leave the
same 72 higher-gain errors. Re-executing the 1.150× receiver with
visits `46/47` and `93/94` yields eight capture timings, all with
the same 12/64 call and 11/64 answer wrong indices. Reject these
simple wire/edge repairs and test explicit multistage phase-bit-0
logic for `48` and `2F` on a fresh holdout; C3/G2 stay active.
The [mode-qualified phase-bit-0 veto](g2/JOINT-MASK04-12A-PHASEBIT0-VETO.md)
now clears the original gate's false bit 0 at `48`/`2F` with two
explicit terms. It fits 42 observed mode-conditioned labels and all
22 development streams. Four new real-PROM call/answer fixtures
recover exact modeled serial/executed controller bytes: phase-137/139
carrier transfers do not activate the veto, while new phase-131
payloads at 1.15× and 1.25× do, changing original 17/12 and 15/17
dibit errors to 0/64 in each selector. The 1.15× holdout has no
modeled clipping; the 1.25× holdout has 4/2 clipped samples. No
holdout reaches an unseen state and the extra veto package/nets are
unassigned. Challenge unseen predictions and a photo-compatible
gate realization; keep C3/G2 open.
The [phase-133 matched low-gain challenge](g2/JOINT-MASK04-12A-PHASEBIT0-LOWGAIN-FAILURE.md)
now finds a genuine unseen-state failure of that frozen veto. With
identical real-PROM transmitter bytes and receiver PC path, calibrated
gain avoids `1D` and recovers exact controller bytes; 0.8× gain visits
`1D`, misses 4/64 call and 7/64 answer dibits, and delivers wrong
bytes without clipping. Eleven adjacent transitions require `1D`
phase 0, but the package/veto circuit assigns 1; the old cover
happens to assign 0. Do not promote the two-term fix to C3. Test a
richer photo-compatible state/timing input against both low- and
high-gain fixtures, then challenge a frozen route on fresh real-PROM
data. C3/G2 stay active.
The [adjacent-visit low-gain replay](g2/JOINT-MASK04-12A-LOWGAIN133-EXPANDED-VISITS.md)
preserves the failed real-PROM traces while adding visits `47`, `94`
and `141`. All six `1D` occurrences give `3F8` Y=`4F` at visit `94`;
visit-`141` row Y=`9F` also occurs in 24 opposite-bit symbols, and its
`3F8` Y varies within `1D`. This identifies a timing feature to test,
not a new physical decoder. Capture visit `94` on the older mode-1
controls before designing a frozen consumer, then challenge fresh
carrier/gain data. Keep C3/G2 open.
The [visit-94 phase-bit screen and holdout](g2/JOINT-MASK04-12A-VISIT94-PHASE-GATE.md)
now supply that control and challenge. Replayed phase-131 1.15×/1.25×
mode-1 streams give visit-`94` `3F8` Y=`AF` at state `48` and `2F` at
state `2F`, while low-gain `1D` gives `4F`. A frozen later-capture Y6
veto activates on `1D` but not those higher-gain states. Four fresh
real-PROM call/answer streams at 0.8× gain and carrier starts `133`/`135`
reduce 23 total old-veto dibit errors to zero, recover exact modeled
line/controller bytes and show no clipping. This is conditional C3
evidence: visit-`94` storage, extra gates and the serial/line nets are
still assumptions, and the holdout reached no other unseen state. Test
package-compatible capture/logic and a further unseen-state gain/carrier
family before C3 acceptance; keep G2 active.
The [staged U14/U12/U3 capture replay](g2/JOINT-MASK04-12A-VISIT94-LATCH-ROUTE.md)
now supplies one photo-package-compatible storage schedule. U14's
independent latch pairs hold first Y5/Y7 while first Y6 is copied to
U12 at visit `47`; U14 then reuses its Y6 latch at visit `94`, and U3
holds the visit-`93` bits. Across ten saved real-PROM streams and 650
symbols, the staged state, decisions and controller bytes match the
earlier candidate; row-0 Y0 is stable from visits `46` to `47`.
A common-enable overwrite of U14's first Y5/Y7 at visit `94` causes
22–29 dibit errors per stream, so the independent pair enables matter.
The specific data/enable nets and full phase-gate package budget remain
unknown, so keep C3/G2 open and test them as explicit assumptions.
The [carrier-141 gain challenge](g2/JOINT-MASK04-12A-VISIT94-CARRIER141-FAILURE.md)
then rejects the frozen later-capture gate outside its earlier carrier
family. Four new real-PROM streams at 0.7×/0.8× gain have 19/22 and
6/14 dibit errors, wrong line/controller bytes and no modeled clipping.
The matched gain pairs retain identical transmitter and receiver PC
digests. A joined phase graph localizes the new gate's wrong predictions
to states `0A`, `4A`, `53`; older and newer runs also disagree on `0D`
under the current collapsed `81/A1` mode assumption. Replaying the
older answer run shows visit-`94` Y6 varies within `0D`, and the frozen
gate adds seven errors there. Test held `81` versus `81→A1` on the same
carrier-141 waveform before trying more Boolean terms; keep C3/G2
active and the physical wiring assumptions explicit. The matched
held-`81` control now does that: it preserves the same Tx/raw/PCM
waveform, changes the receive states, but leaves 15/23 candidate dibit
errors and wrong controller bytes. State `0D` with later Y6=1 still
requires phase 0 in the joined graph, versus phase 1 in the older
held-`81` answer fixture. The direct mode byte alone does not explain
that conflict. Test carrier/timing history or another constrained
receive signal; do not add a per-state patch.
The [early-bit phase graph](g2/JOINT-MASK04-12A-EARLY-BIT-PHASE-GRAPH.md)
now compares full five-visit old/new `0D` captures. First `3F8` Y4
and row-0 Y1 at visit `46` each separate every older phase-112 `0D`
from every newer carrier-141 `0D` under both held and switched mode.
Across 18 real-PROM streams, the original seven-bit graph has 116
directed conflicts; either early bit yields one 24-state component
with zero conflicts, while visit-`94` Y6 leaves 16. Row-0 Y1 is stable
through visit `47` in all 1,170 symbols, so an assumed third U12 FF
is one package-capacity route. Freeze an early-bit state candidate and
challenge fresh data/carrier/gain before treating it as a receiver
decision; C3/G2 remain active.
The [frozen row-0 Y1 holdout](g2/JOINT-MASK04-12A-ROW1-PHASE-HOLDOUT.md)
now tests that candidate on four new real-PROM/controller streams at 0.75×
gain. Both carrier-`141` selectors recover exact dibits, line bytes and
executed controller payloads; both carrier-`143` selectors reach two unseen
keys and have five/four wrong transitions even between known keys, without
clipping. The one-bit table therefore does not transfer across this carrier
change. A 22-stream screen finds no conflict-free single captured bit, while
row-0 Y1 at visit `46` plus `3F8` Y4 or Y5 at visit `94` yields a
conflict-free development graph. Freeze one photo-compatible two-bit capture
route for a new holdout; keep the nets conditional and C3/G2 active.
The [two-bit phase holdouts](g2/JOINT-MASK04-12A-TWO-BIT-PHASE-HOLDOUT.md)
now test row-0 Y1 at visit `46` plus `3F8` Y4 at visit `94`. A frozen
31-code table meets new keys `1DB` and `1CC` on carrier-`145/147`
streams but makes no errors between known keys. Those streams extend a
conflict-free graph to 33 codes; their exact controller replay is
development evidence because it supplies the new labels. The enlarged
table, frozen before four new carrier-`149/151` real-PROM/controller
streams, then recovers all 64 dibits and exact modeled line/controller
bytes in each, without clipping. Test another gain family and a
photo-package-compatible gate/latch realization; C3/G2 stay active and
the physical nets remain assumptions, not blockers.
The [matched-gain two-bit challenge and logic screen](g2/JOINT-MASK04-12A-TWO-BIT-GAIN1-LOGIC.md)
now changes only receive gain on the carrier-`149/151` payloads: all
four calibrated-gain streams retain the same Tx trace but reach three
new nine-bit states, with zero wrong known-state transitions and no
clipping. A 36-code table fitted to those states then meets a further
new state `05C` on four fresh carrier-`153/155` streams, again with no
wrong known-state transitions or clipping. The 38-stream phase graph
remains conflict-free at 37 codes; exact replays of the newly labelled
streams are development evidence. An exhaustive observed-state SOP
screen requires at least five products for one phase bit under any
global phase offset, exceeding U15's four direct AOI products. Freeze
the 37-code table for a new gain-1 holdout and test a multistage
photo-package-compatible gate; keep C3/G2 active.
The [frozen 37-code calibrated-gain holdout](g2/JOINT-MASK04-12A-TWO-BIT-GAIN1-37-HOLDOUT.md)
now adds four new carrier-`157/159` real-PROM/controller streams. All
reach unseen keys, but there are no errors between known keys or clipped
samples. The joined 42-stream graph remains conflict-free at 42 codes;
the exact controller replays after labelling the five new keys are
development evidence. The previously frozen observed-state SOP predicts
four of those five keys but misses `1ED`; a new exact SOP screen still
requires at least five products for one phase output. Pursue a
multistage photo-compatible circuit and test it on untouched data;
keep C3/G2 active rather than treating expanding state coverage as a
blocker.
The [revised package-capacity receive route](g2/JOINT-MASK04-12A-TWO-BIT-PACKAGE-ROUTE.md)
now uses U12/U14 complementary Q outputs, U13's two inversions, one
U15 AOI, all three U19 NANDs and three U21 NORs to compute both phase
bits from the nine-bit state. Its first frozen version passes the new
carrier-`161` unseen state but fails `101`/`141` at carrier `163`, with
17/13 wrong dibits and wrong controller payloads despite zero USART
status errors. Replacing one U15 input term yields a revised circuit
that fits the resulting 45 observed states. Frozen before carrier
`165/167` runs, it predicts unseen `035` and recovers exact dibits,
modeled line bytes and executed controller payloads in all four new
streams, without clipping. A staged U14/U12/U3 replay matches 3,250
symbol states across 50 streams and leaves 2,929 modeled cycles before
RxC. The photographed packages support this capacity hypothesis; their
actual nets and the analog/USART path remain untraced. The matched-gain
challenge below tests that route at another signal level; C3/G2 stay
active.
The [matched 1.15× gain challenge](g2/JOINT-MASK04-12A-TWO-BIT-PACKAGE-ROUTE.md)
now holds the carrier-`165/167` transmitter traces and payloads fixed
while changing receive PCM/PROM traces. The same frozen package circuit
predicts four new nine-bit states and recovers every dibit, modeled line
byte and executed controller payload across all four higher-gain runs,
without clipping. Their staged latch states also match. This strengthens
the conditional C3 route across signal level; test a distinct clock or
mode boundary and constrain the actual nets before acceptance. Keep
G2 active.
The [matched mode-boundary control](g2/JOINT-MASK04-12A-TWO-BIT-PACKAGE-MODE-CONTROL.md)
now holds the carrier-`165/167` Tx, PCM and PC path fixed while offering
held `81` or moving the assumed `3EB` `81→A1` edge from symbol 32 to
48. The frozen nine-bit gate makes 8/10 and 11/13 dibit errors under
held `81`, then 4/4 and 4/6 under the late edge; all wrong transitions
touch `01C` and occur before the later edge. The joined nine-bit graph
has 102 conflicts across 58 streams. Adding the imposed mode bit 5 or
first `3F8` Y4 at visit `46` removes them. U14/U12 have a plausible
spare-latch/fourth-FF storage schedule for early Y4, but its full gate
is not yet package-realized. Freeze and challenge a mode-qualified or
early-Y4 circuit; keep C3/G2 active and the nets assumed.
The [ten-bit package-gate held-81 challenge](g2/JOINT-MASK04-12A-TEN-BIT-PACKAGE-MODE.md)
now tests a later-Y6 capture alternative. A first photographed-package-budgeted
gate fails new `32C` at carriers `169/171`. A revised gate fits those
development streams, then passes two fresh carrier-`173` cases with unseen
states but fails both carrier-`175` cases at new state `12D` (12/64 wrong
dibits each and wrong controller payloads, without clipping). The expanded
60-state graph has zero conflicts but two disconnected components. Reallocate
the occupied U15 arms or test another photo-compatible capture while keeping
physical nets assumed; neither failed gate blocks C3/G2 experiments.
The [ten-bit product-bound audit](g2/JOINT-MASK04-12A-TEN-BIT-PACKAGE-MODE.md)
proves that phase bit 0 needs five direct product terms for either global
phase polarity on the expanded 60-state graph; U15 supplies only four AOI
arms. A direct arm swap cannot resolve `12D`. The same 66-stream screen
finds 24 conflict-free alternate captured bits, including connected graphs
for first `3F8` Y4, later `3F8` Y7 and visit-`141` Y6. Test their package
logic or a multistage route, then challenge fresh data; keep C3/G2 active.
The [mode-bit graph and matched-mode challenge](g2/JOINT-MASK04-12A-MODEBIT66-HOLDOUT.md)
now replaces later-Y6 with an explicitly assumed `3EB` mode bit. Its
66-stream phase graph has 61 connected states and zero conflicts, but phase
bit 0 needs six or seven direct product terms, beyond one four-arm U15
output. A frozen Boolean cover passes fresh held-`81` call/answer streams,
including unseen `0C2`, with exact dibits, line bytes and controller payloads.
It fails fresh edge-at-32 streams with 16/15 dibit errors. Every wrong
transition touches an unseen state; a joined 70-stream graph remains
conflict-free and identifies one wrong phase label at `32D`. Treat those
streams as development data, freeze a revised decoder and challenge new
payloads and carrier starts. The mode connection and gate packages remain
assumptions; C3/G2 stay active rather than blocked.
The [frozen `32D` revision and offset-179 challenge](g2/JOINT-MASK04-12A-MODEBIT66-HOLDOUT.md#frozen-revision-and-independent-offset-179-challenge)
now passes four untouched held/moving-mode real-PROM streams: 0/64 dibit
errors in each, exact modeled line bytes and executed-controller payloads,
and unseen `099`/`2D9` states. The old gate would fail the two moving-mode
streams, so the correction is exercised. Keep the mode net and multistage
gate/serializer timing as testable assumptions; establish a package-budgeted
circuit and challenge other mode boundaries, gains and carrier phases before
passing C3. G2 remains active.
The [package-delta audit](g2/JOINT-MASK04-12A-MODEBIT66-HOLDOUT.md#frozen-revision-and-independent-offset-179-challenge)
shows the old nine-bit photographed-package network already matches 60/64
revised phase labels. Its four exceptions need two distinct correction
decodes, of at least four and five literals on the observed states. The
old U19 and U15 allocation is full; the visible U7 NAND and spare U13/U21
gates are candidate resources, not a demonstrated complete circuit.
Test a rewired or multistage package realization and its timing; the
unassigned nets are an experiment, not a G2 blocker.
The [fresh late-boundary control](g2/JOINT-MASK04-12A-MODEBIT66-HOLDOUT.md#fresh-late-boundary-control)
now moves the imposed `3EB` edge from symbol 32 to 48 with new offset-181
payloads. The frozen revised decoder recovers all four real-PROM streams
with 0/64 dibit errors, exact modeled line and controller bytes, and unseen
states. Matched Tx/PCM/PC digests isolate the changed Rx input. Keep C3
open for a complete package/serial route and test a different gain and
carrier phase next; the untraced mode net does not block those tests.
The [fresh 0.8× lower-level challenge](g2/JOINT-MASK04-12A-MODEBIT66-HOLDOUT.md#fresh-lower-level-and-mode-boundary-control)
then changes carrier start and payloads while pairing edges at symbols
32 and 48. All four real-PROM/controller runs recover 64/64 dibits and
exact modeled line/controller bytes without clipping, including five
previously unseen states in the late-edge pair. This is stronger
conditional C3 evidence across gain; a high-level challenge and a
complete package/serial implementation remain open experiments, not
reasons to block G2.
The [higher-level challenge and capture screen](g2/JOINT-MASK04-12A-MODEBIT66-HOLDOUT.md#higher-level-failure-and-extra-capture-bit)
now locate a real limit of that frozen decoder. At 1.25×, both mode
boundaries miss 23/17 call/answer dibits despite exact independent
reference decisions; each stream clips twice. A matched 1.05× control
still misses 11/10 with **no** clipped samples, although its call-side
reference has one error. Across 92 saved streams, the ten-bit phase
graph has 314 conflicts, so relabeling it is insufficient. Adding one
photo-compatible row-0 Y2 capture at visit 93 or 94 yields a connected,
conflict-free 91-state graph, including the 89-stream subset after the
three known reference-error runs are excluded. Freeze an eleven-bit
Boolean decision and challenge fresh data. The added row-0 Y2 is a
**late** value, different from the early U12 capture in 3,144/5,980
symbols; U12's common clock means its spare FF alone cannot preserve
early Y0/Y1 while taking that late bit. Test a separate storage or
timed-transfer route and its gate/serial timing as explicit assumptions.
C3/G2 remain active, not blocked by missing pin continuity.
The [frozen eleven-bit phase holdouts](g2/JOINT-MASK04-12A-MODEBIT91-HOLDOUT.md)
now test late row-0 Y2 as the extra captured signal. A 17-product
Boolean cover fits 91 observed development states; it is not a
package-realized decoder. Fresh 1.25× offset-187 streams recover exact
dibits and controller bytes across both mode boundaries, but reach only
known states. Fresh unclipped 1.10× offset-189 edge-32 streams pass on
unseen states, while matched edge-48 streams miss four dibits per
selector. Three wrong transitions per stream join known states, and the
joined 96-stream eleven-bit graph has 132 conflicts. Screened late-Y7
and late-row alternatives remove these conflicts as new hypotheses;
freeze one, run untouched data, and test its storage/gate/serial timing.
The failed candidate and untraced nets do not block G2.
The [frozen twelve-bit late-Y7 holdout](g2/JOINT-MASK04-12A-MODEBIT97-HOLDOUT.md)
now adds visit-94 `3F8` Y7 to resolve those development conflicts.
Its 97-state graph is connected and conflict-free; an 8/5-product
Boolean cover fits all 96 development streams but is not a photographed
gate circuit. On fresh offset-191 1.10× data, both mode edges recover
exact modeled line and executed-controller bytes with 0/64 gate errors,
no clipping, and unseen states. The independent answer reference is
exact; the call reference misses two dibits, so keep the call-side
interpretation conditional. Test another carrier/level and a timed,
package-budgeted Y2/Y7 storage, gate and USART path. C3/G2 remain open
and active; missing physical continuity is not a blocker.
The [staged twelve-bit capture replay](g2/JOINT-MASK04-12A-MODEBIT97-HOLDOUT.md#photo-package-capacity-replay)
now assigns the capture bits across photographed U3/U12/U14/U25 storage
capacity. On 100 saved real-PROM streams (6,500 symbols), staged values
match direct states with zero decision mismatches and 2,929 modeled cycles
between the last capture and the assumed first RxC. This tests a storage
schedule, not a complete circuit: U25 is no longer available for the older
assumed previous-phase memory, the mode-bit hold and actual data/clock nets
are untraced, and the Boolean gate/USART path is unallocated. Continue with
alternative package allocations and a timed serial-output hypothesis while
C3/G2 remain active. Treat each failed allocation as a result, not a blocker.
The first alternate allocation has a concrete negative result: sampling the
preceding final phase into U3's spare latches at its visit-93 second-Y clock
would see a mixed old/new state. The frozen gate disagrees with that prior
phase on 1,268/6,400 tested transitions. Try a separately held phase signal,
another register or a different capture clock; keep G2 active.
The [U28 four-bit pipeline replay](g2/JOINT-MASK04-12A-MODEBIT97-HOLDOUT.md#u28-phase-and-dibit-pipeline-hypothesis)
now supplies one such register allocation: assumed synchronous load at
cycle 4,500 stores the new phase and both outgoing bits together. It
matches 6,400 decisions and 13,000 serial bits across the saved streams;
loads before the late captures or after first RxC fail their timing
controls. This removes the U25 storage conflict **within the model**, not
the untraced clock/data nets or gate-budget problem. Test the subtraction
and bit selector as package-budgeted circuits, then run a new signal
fixture. C3/G2 stay active.
The [new level and capture screen](g2/JOINT-MASK04-12A-MODEBIT102-LEVEL-SCREEN.md)
now challenges that receiver state family at fresh 1.05× and 0.95×
levels. An exact seven/five-product cover fitted through offset 191
fails on unseen `2DE` at 1.05×, while the older eight/five cover passes
all four real-PROM/controller runs. A post-hoc seven/old-five combination
then fails the untouched 0.95× runs at the same indices as the older
gate: the joined 102-state twelve-bit graph has 218 conflicts. Only
visit-141 `3F8` Y4 or Y6 among 76 screened extra bits removes them.
That capture arrives at modeled cycle 4,575, after the assumed U28 load
at 4,500; U3's shared latch cannot be re-enabled without overwriting
second-visit bits. Test a later U28 load with a justified data-hold path
or separate late-bit storage, then freeze a new gate for untouched data.
These failed fixtures and untraced nets keep C3 open, not G2 blocked.

The [full-stream bank-phase screen](g2/JOINT-MASK04-TX-BANK-PHASE.md)
now finds that `12A` Y bit 0 changes on 75,012/75,018 raw call/answer
visits when `129` A8 changes, and **every** one of 375 fixed divided-clock
phases captures changed bytes. At phase 0, 198/202 of 832 candidate
samples differ by 16 DAC counts in all six surviving bus orders, while
both banks retain the 2,100 Hz tone and 0/62 filtered A3/A4 errors.
This supplies a ROM-sensitive `12A` output hypothesis; constrain the
latch edge, Y data path and analog node before treating it as the line.
Keep C2 open and G2 active.
The [raw-edge timing comparison](g2/JOINT-MASK04-TX-BANK-EDGE-TIMING.md)
shows why the capture phase matters: across 1,014 U10 D2 rises at `129`
and falls at `12A` in a held-tone run, the preceding `128`/`129` Y bytes
never show the bank switch, while settled `12A` Y differs 221 times.
Use a photo-compatible post-`12A` data-capture hypothesis, or independently
constrain CLK/data timing; a pre-edge latch does not establish this
ROM-sensitive output path. The uncertain clock is a testable assumption,
not a G2 blocker.
The [two-bit `12A` PROM-gate replay](g2/JOINT-MASK04-TX-12A-GATE.md)
supplies a concrete alternative clock hypothesis: `U11.D0 & U17.D1`
is high only at `12A` among all 39 PCs reached in the full call and answer
transmitter runs, so a NAND rises at `12A→127`. A latch on that edge can
capture settled `12A` Y if the PROM gate changes before the next ALU Y;
the paired bank run has 221 changed bytes on 1,013 observed edges.
Test the counter-qualified edge with explicit gate/Y delay ordering and
the six DAC buses. Keep the untraced wiring as an assumption, not a blocker.
The [full delayed-latch replay](g2/JOINT-MASK04-TX-12A-DELAYED-LATCH.md)
now tests both orders over the complete call and answer controller streams.
Capturing preceding `12A` Y at every 375th NAND edge changes 198/202 of
832 candidate DAC samples under the ROM-bank switch and gives a 2,100 Hz
A1 peak plus 0/62 A3/A4 errors on all six bus orders. Capturing settled
`127` Y after a later edge gives no bank-sensitive samples and 0–3 data
errors, depending on selector and bus. The early gate/Y ordering is now
a precise requirement for a **direct** 74LS273 clock; test its timing or
an intervening hold stage, and keep C2 open until the route is constrained.
The [two-stage 74LS373→74LS273 replay](g2/JOINT-MASK04-TX-12A-TWO-STAGE-LATCH.md)
now tests that alternative in four full call/answer × ROM-bank executions.
An assumed 74LS373 transparent only at `12A` holds settled Y after its
enable closes on `12A→127`; a three-bit raw-PROM decode can clock the
74LS273 later at `127→128` in the tested loop. Every 375th held sample
retains the 198/202 bank-sensitive bytes, while a transparent-through-`127`
control retains none. The proposed 127 decode has seven full-store hits,
so it is mode-specific. This supplies a concrete late-clock circuit
hypothesis without identifying the latch pins, divider, DAC or analog route.
Test those photo-compatible nets and timing alternatives; C2/G2 stay active.
The [DED latch-bus photo audit](g2/PHOTO-DED-LATCH-BUS.md) finds eight
threshold-stable visible front-side tracks between the 74LS273 and
74LS373 pad banks. The image does not establish their pad continuity,
direction or Q→D staging. The
[B5 topology comparison](g2/JOINT-MASK04-TX-LATCH-B5-DISCRIMINATOR.md)
therefore runs two explicit continuations on the same real-PROM controller
streams: a 74LS373 hold of `12A` Y followed by a 74LS273 clock at
`127→128`, and a shared Y-input bus on which the 74LS273 instead samples
settled `127` Y. Under the untraced Y4→74LS273 D4 assumption and the
photo-suggested Q4→DAC08 B5 connection, these routes predict different
B5 levels on 698/832 call and 696/832 answer sample clocks. The normal
stream is thus a useful discriminating stimulus even without a new ROM-bank
switch; that switch affects B4, not this B5 segment. Next test another
photo-compatible data/clock route or independent pin/line constraint, with
the same controller stimulus and a changed-edge control. Until physical
continuity or an independent observation chooses a route, keep both
topologies conditional and C2/G2 active. The ambiguous tracks do not block
further work.
The [fresh latch-topology line challenge](g2/JOINT-MASK04-TX-LATCH-TOPOLOGY-LINE-CHALLENGE.md)
now scores held-`12A` and shared-live-`127` samples from the same real-PROM
trace on new call/answer payloads encoded by the established line-side
scrambler model, using the previously fixed
Q=0.5 line stage, +6 alignment and zero-run gains. Across all six DAC bus
orders, held `12A` makes 0/64 errors per selector, while live `127` makes
5/64 call and 1/64 answer errors at nominal unclipped gain; the counts
persist at 0.75× and 1.25×. This disfavors the exact shared-live-`127`
route under that analog model. Constrain the latch data/clock or DAC pin
path independently before passing C2; keep G2 active.
The [executed-controller A4 topology check](g2/JOINT-MASK04-TX-LATCH-CONTROLLER-LINE.md)
now repeats that comparison with the saved 8031-produced segment-2 bytes
and real-PROM Tx traces. At the fixed Q=0.5 line stage, held `12A` makes
0/62 A3/A4 decision errors for each selector and all six buses; live
`127` makes 1/62 call and 2/62 answer errors, while both retain the
2,100 Hz A1 peak. This supports the conditional held route on executed
controller traffic but leaves the latch, DAC and analog nets to constrain;
C2/G2 stay open.
The [latch-gap pin-function audit](g2/PHOTO-DED-LATCH-BUS.md#pin-function-audit-of-the-visible-tracks)
now aligns the eight visible front-side tracks with four Q–Q and four D–D
74LS273/74LS373 pin pairs. None is a visible 373-Q→273-D copy link under
that photo assignment. This weakens the simple serial-hold circuit used to
obtain the successful held-`12A` waveform. Test the direct 74LS273
clock-before-new-`127`-Y route and any back-side continuation explicitly;
do not equate a good modeled line score with identified wiring. C2/G2
remain active.
The [whole-store `12A` PROM-gate audit](g2/JOINT-MASK04-TX-12A-FULL-STORE-GATE.md)
now tests the direct 74LS273 clock alternative. The prior two-bit decode
selects 111 store words, including eight in the receive-address span.
Adding `~U18.D1` removes all `3E0–3FF` aliases; adding `U17.D3` isolates
`12A` across the full 1,024-word store. The four-literal product is
minimal, while every all-positive product aliases other words. A direct
capture still requires the old `12A` Y to meet the 74LS273's 20 ns setup
and remain unchanged for 5 ns after the clock; those propagation margins
and nets are unmeasured. Test the gate/counter/clock timing and late-edge
control under these explicit assumptions; keep C2/G2 active.
The [ROM-sensitive buffered-line replay](g2/JOINT-MASK04-12A-BUFFERED-LINE.md)
now substitutes the `12A` latch into the full controller-bit/PROM path.
At the existing six-sample alignment, an independent line decoder gives
1/64 call and 0/64 answer errors on all six photo-compatible DAC buses.
Separate real-PROM receiver runs sustain both streams, but all three
frozen fixed-pair readouts and the frozen margin selector leave wrong or
unknown data dibits, so no full eight-byte USART handoff occurs on this
ROM-sensitive route. Develop a new receiver readout on independent data
and retest here; constrain the call-line decision and physical DAC route.
C2/C3 stay open, and these incomplete connections remain runnable
assumptions rather than goal blockers.
The [extended alignment test](g2/JOINT-MASK04-12A-EXTENDED-SHIFT.md)
preserves the original 846 `12A` samples, adds six held-tail samples, and
tests offsets +4 through +12. No added offset makes the call reference
decoder exact on any of the six candidate DAC buses: +6 has one error at
index 35, and +7 still has one or two errors at other indices. This
excludes tail-only alignment as the repair for the original Q=1 fixture.
The missing DAC/analog trace is a labelled assumption, not a blocker.
The [bounded analog screen and holdout](g2/JOINT-MASK04-12A-ANALOG-HOLDOUT.md)
find a fixed 1950 Hz, Q=0.5, peak-110, +6-sample line candidate with
0/64 call and 0/64 answer reference errors on all six buses. Four new
nonzero controller-fed streams also give 0/64 each on all six buses;
the prior Q=1 control fails two streams. This resolves the call-line
reference discrepancy for a conditional analog route. The
[fixed-gain phase check](g2/JOINT-MASK04-12A-FIXED-GAIN-PHASE.md)
calibrates gain on the zero-run only, then keeps it across both saved
nonzero payloads per selector. At +6, all 24 bus/payload streams are
exact at 75%, 100% and 125% of that gain. At +5, six stream/bus cases
miss one answer dibit; +7 fails all 24. Constrain the latch/sample
alignment. The [full-byte phase replay](g2/JOINT-MASK04-12A-FULL-BUS-PHASE.md)
now checks the executed `12A` candidate directly on both buffered
controller streams and all six surviving DAC orders. Their raw A1 byte
streams peak at 2,100 Hz and all 31 A3 adjacent-symbol steps are ±180°.
The raw eight-sample A4 phasors can miss a quadrant by 48–63°, but the
previously fixed Q=0.5/+6 line fixture and matched symbol window put all
32 data steps per selector/bus within 40.1° of the intended quadrant.
These are conditional digital/analog-model signatures, not identified
DAC08 current or line output. Constrain the latch and physical line route;
keep C2 open and G2 active. The
[receiver-oscillator mismatch check](g2/JOINT-MASK04-12A-CARRIER-MISMATCH.md)
keeps the line and zero-run gain frozen: all 24 bus/payload scores
remain exact at reference-local offsets −14, −7, 0, +7 and +14 Hz.
This removes a small *reference receiver* mismatch as an explanation
for the earlier data error; it does not test DSC carrier recovery or
the board's actual transmit-frequency offset. Test those executed
paths without refitting, and seek a photo-compatible line/ADC and
DSC-to-USART consumer. The
external known-carrier decoder does not establish physical filter Q or
complete C2/C3.
The [Q=0.5 receiver replay](g2/JOINT-MASK04-12A-Q05-RECEIVER.md)
feeds one new nonzero payload per selector through the real-PROM mask-04
receiver, using the exact line PCM hashes that scored 0/64 in the
independent reference decoder. All four frozen readouts remain
incomplete: the no-wrong 46/93 rule has 27/32 call and 22/32 answer
data dibits unknown; the margin rule has fewer unknowns but wrong
decisions. The [executed-key audit](g2/JOINT-MASK04-Q05-RECEIVE-KEY-COLLISIONS.md)
finds five conflicting primary 46/93 keys on those 64 data dibits,
but sixteen conflict-free alternate 46/93 transition keys forming
four phase states. A [frozen four-state rule](g2/JOINT-MASK04-Q05-PHASE-STATE-HOLDOUT.md)
then decodes the *second* nonzero payload in each mode: 128/128
holdout dibits, all sixteen line bytes, and the exact eight decoded
controller payload bytes per mode with aligned assumed SYNDET. Early
and late pulses fail their controls. This joins the ROM-sensitive Tx,
real-PROM Rx and unchanged 8031 on fresh data under a compact external
consumer. C3 stays open: identify or test a photo-compatible phase
logic, latch, RxD/RxC and SYNDET route, rather than treating that
consumer as an executed DSC instruction or verified wiring.
The [fixed-gain level challenge](g2/JOINT-MASK04-Q05-PHASE-LEVEL.md)
shows why the first four-state rule was incomplete: at 75% line level
new states `9/B` leave 17/32 data dibits unknown per selector, and at
125% new state `6` leaves 14/32 call and 18/32 answer unknown, even
though the independent line decoder stays exact. The executed
transitions across all six runs admit consistent new phase labels
`6→0`, `9→1`, `B→2` with no key collisions. A
[call-trained, answer-held-out extension](g2/JOINT-MASK04-Q05-PHASE-LEVEL-MAP.md)
recovers 64/64 dibits and exact aligned modeled 8031 payload bytes in
all six level/mode cases. The two selectors use different scrambled
line streams but the same decoded payload. Challenge the frozen seven-
state rule on fresh payloads and phase starts, then constrain its
photo-compatible logic and serial timing; C3 remains open.
The [fresh-payload level replay](g2/JOINT-MASK04-Q05-FRESH-PAYLOAD-LEVELS.md)
now freezes that seven-state rule and tests one previously unused
eight-byte payload per selector, each at 75%, 100% and 125% fixed
zero-run gain. All six real-PROM Tx→line→Rx runs recover 64/64
dibits and eight exact line bytes; the modeled 8251/8031 descrambles
each payload only with aligned assumed SYNDET. Both fresh data streams
exercise all four dibits. This strengthens the conditional C2/C3
chain but does not identify the physical DAC/ADC, phase combinator,
capture/serializer or RxD/RxC/SYNDET route. The [running R1 phase
challenge](g2/JOINT-MASK04-12A-RUNNING-PHASE.md) shows that an initial
R1 seed does not alter sampled `12A` output, while a one-time `40`
offset during data changes all 65 executed receive phase states in
each mode. The frozen rule still recovers 64/64 dibits and exact
modeled controller payloads without refitting. A `20` offset makes
one to three reference errors at the first data boundary. The
[half-quadrant timing test](g2/JOINT-MASK04-12A-PHASE-TIMING.md) moves
that `20` step into the muted interval, but the same reference errors
remain. Its frozen seven-state receive rule fails on the new `2,6,9,D`
state family. A unique call-constrained four-state relabeling recovers
64/64 dibits, exact line bytes and both modeled controller payloads on
the answer holdout without refitting; no executed or photographed
phase-normalization mechanism has been identified. The
[controller A4 calibration replay](g2/JOINT-MASK04-12A-A4-PHASE-TRAINING.md)
resolves the data-leakage concern: the constant preamble constrains no
phase labels, but the independently known 32-dibit V.26 ter A4 pattern
selects one of 64 maps for the offset-`20` receiver. Without using
fresh-payload answers, that A4-trained map recovers 64/64 dibits and
exact modeled controller payloads in both saved call/answer runs.
The [joined A4/data replay](g2/JOINT-MASK04-12A-JOINED-A4-DATA.md)
now runs the known 32-dibit A4 pattern followed by 32 fresh data
dibits in one continuous real-PROM transmitter and receiver line
fixture per selector. Each A4 segment alone selects one of 64 phase
maps; it decodes the immediately following data 32/32 and recovers
all eight line bytes without payload-label fitting. The controller
A4 and payload bytes still came from separate fixtures, and a
16-byte 8251/8031 handoff was not run. The
[controller continuation](g2/JOINT-MASK04-12A-CONTROLLER-CONTINUATION.md)
now takes the first 129 bits of consecutive A4/A5 port-01 writes from
one unchanged 8031 run, aligned at the independently verified
segment-2 bit. Both sustained real-PROM DSC Tx→line→Rx replays learn
one map from A4 and recover the next eight A5-derived bytes exactly.
That controller fixture forces timer expiry and USART-ready status.
The [17-character paced TxD replay](g2/MAIN-LOOP-USART-TXREADY-17.md)
now uses the Timer-1/one-byte-8251 model instead: across both selectors
and all eight sampled Tx clock phases, its first 17 **shifted** bytes
equal the controller writes, and TxD bits 1–128 exactly equal the
16-byte input of the joined DSC replay. This closes the modeled
write-versus-shift gap, while TxD-to-DSC wiring and bit alignment
remain assumptions. Next feed the paced bit events with timing into
a photo-compatible DSC serial-input circuit, and test a plausible
ADC/latch/clock phase-decision path. The [16-character reverse handoff](g2/JOINT-MASK04-12A-16BYTE-REVERSE-HANDOFF.md)
now reads all 64 joined dibits from the executed DSC receiver states,
then clocks their exact 16 bytes through a one-byte-buffer 8251 model
to the unchanged 8031. Aligned SYNDET consumes all 16 with no
overrun and independent descrambler agreement; early and late pulses
misalign. This establishes the modeled reverse path under its stated
timing, while the physical DSC-to-RxD/RxC/SYNDET logic and a natural
8031 A3/A4 receive-state transition remain open C3 hypotheses.
The [fifth-bit receive screen](g2/JOINT-MASK04-12A-FIFTH-RECEIVE-BIT.md)
now tests the photo-compatible two-capture Y readout against 75%,
100%, 125% gain and half-quadrant start phase. Its original four-bit
state pairs conflict on two transition keys. Adding first-visit Y4,
second-visit Y5 or second-visit Y6 yields a zero-conflict development
table; each frozen five-bit table then predicts all 96 decisions in
each separate controller A4/A5 holdout with zero wrong and zero
unknown. This gives a concrete fixed-logic candidate but does not
identify its latch/clock/pin route. The [frozen fifth-bit challenge](g2/JOINT-MASK04-12A-FROZEN-FIFTH-CHALLENGE.md)
then tests two new payloads at a half-quadrant start and 75/100/125%
gain. Both nominal-level runs recover exact bytes and modeled 8031
payloads, but 75% causes known-key errors and 125% leaves many keys
unseen. No single added bit survives all 14 labeled development
cases. Three six-bit two-capture features remove those collisions;
the smallest uses first Y5–Y7 and second Y4, Y6, Y7, with 91 observed
transition keys. Its controller A4/A5 check is reused evidence,
not a fresh holdout. The [frozen six-bit holdout](g2/JOINT-MASK04-12A-FROZEN-SIXTH-HOLDOUT.md)
now tests a third, previously unused eight-byte payload in each
selector at 75/100/125% level with the half-quadrant start. All six
real-PROM Tx→line→Rx replays recover 64/64 dibits and eight exact
line bytes; aligned modeled 8251/8031 handoff returns each exact
source payload without errors or overruns. Both streams contain all
four dibits. All observed transition keys were already in the
91-key development table, so unseen-key and other-start robustness
remain unverified.
The [second carrier-start challenge](g2/JOINT-MASK04-12A-SIXTH-PHASE96.md)
keeps those new payloads, gain levels, feature and 91-key table fixed,
but changes the one-time running R1 offset from 32 to 96. All six
real-PROM Tx→line→Rx runs again recover 64/64 dibits and eight exact
line bytes; aligned modeled 8251/8031 handoff returns the source
payloads without errors or overruns. Output, PCM, receiver traces and
transition sequences differ from the offset-32 runs, but every key
remains within the development table. A third carrier start and a
photo-compatible decision circuit without payload-trained labels
remain useful tests; this phase result does not close C3.
The [one-visit-late capture challenge](g2/JOINT-MASK04-12A-SIXTH-LATE-CAPTURE.md)
keeps phase 96 and the frozen table but moves both `3F8` Y reads from
visits 46/93 to 47/94 at nominal gain. The call run leaves 26/64
data dibits unknown across 16 unseen keys; answer leaves 22/64
unknown across 14 unseen keys. Neither has a known-key error, but
neither yields full line bytes or a controller handoff. This rejects
that late-clock fixture as a complete explanation. Next test a
photo-compatible timing or multi-visit consumer and freeze it before
fresh data; do not treat the untraced latch edge as a G2 blocker.
The [phase-logic test](g2/JOINT-MASK04-12A-PHASE-LOGIC.md) replaces the
91-key interpretation with a stronger DPSK constraint. Across 896
labelled development transitions, 18 observed six-bit states admit one
connected four-phase assignment under only two mirror-image dibit
conventions. A frozen phase-difference decoder matches all 12
third-payload holdouts at offsets 32/96 and 75/100/125% gain, 64/64
dibits each. Separately minimized Boolean covers use three terms per
phase bit and also match those holdouts, but treat 46 unseen states
as don't-cares. At the one-visit-late edge it makes 19 call and 21
answer errors, rejecting that clock for the compact circuit. It
remained a candidate pending an unseen-state and carrier-start test.
The [fresh phase-logic challenge](g2/JOINT-MASK04-12A-PHASE-LOGIC-FRESH.md)
now supplies that test. New eight-byte payloads in both modes, at
untrained running R1 offsets 16 and 80, make the frozen 91-key table
leave 29–63 of 64 receive transitions unknown. The frozen Boolean phase
rule makes 19–24 wrong decisions per run, while an independent
reference decoder is exact in all four. Two new six-bit states occur,
but 16 of the Boolean errors across the four runs involve only
previously known states. Adding either fresh offset to development
leaves no consistent static four-phase assignment under any dibit
convention. This rules out the **static six-bit/two-capture phase
decoder** across these fixtures, not demodulation itself. Try a
photo-compatible carrier/timing-history or extra-visit consumer,
then freeze it for untouched data and phase starts; do not block on
the untraced clock or logic route.
The [seventh-bit phase screen and holdout](g2/JOINT-MASK04-12A-SEVENTH-PHASE.md)
tests the saved full Y bytes at 46/93. With the offset-16/80 failures
now counted as development, adding either first Y4 or second Y5 is
enough to remove all four-phase graph conflicts; the full two bytes
are also consistent. Both seven-bit graphs have three independently
rotatable components. Frozen candidates then face a fourth payload
pair at new offsets 48/112. First-Y4 makes no known-component errors
but abstains on 26–59 of 64 decisions; second-Y5 makes 3–6 errors
and also abstains widely. Neither yields full line bytes. Using the
new labels post hoc, first-Y4 still admits a phase assignment, while
second-Y5 has 86 combined conflicts. Keep first-Y4 as a conditional
feature candidate, explicitly move these failures into development
before any refit, and validate on fresh payloads/starts. In parallel,
test a photo-compatible third capture or carrier-history signal that
predicts unseen states without fitting their labels. C3 stays open.
The [multi-visit row-phase test](g2/JOINT-MASK04-12A-MULTIVISIT-PHASE.md)
reruns the conflicting offset-16/80, baseline offset-32/96 and 75%-gain
fixtures with real-PROM snapshots at visits 46/47/93/94/141. Across
12 cases the six-bit state has 40 phase-graph conflicts. A 120-candidate
single-bit screen finds 42 zero-conflict alternatives, but no
visit-141 bit removes the conflicts. A concrete `3ED` row-0 bit-0
candidate at visit 46 yields one connected 11-state phase map and is
distinct from the earlier Y bits. Frozen on new payloads at offsets
0/64, it makes no known-state errors but leaves 28–63 of 64 decisions
unknown because states `08`, `0C` and `55` were absent from training;
the old six-bit lookup and independent reference are exact on those
particular runs. The row candidate remains structurally consistent
after a post-hoc 14-state extension, but that extension is a new fit,
not validation. Seek a photo-compatible latch/timing or carrier-state
rule that predicts new states, then use untouched payloads and starts.
Do not treat the missing net continuity as a G2 blocker.
The [frozen row-0 Boolean holdout](g2/JOINT-MASK04-12A-ROW0-BOOLEAN-HOLDOUT.md)
uses those offset-0/64 failures as explicit development, then fits a
small four-phase decoder to 14 observed states: phase bit 0 needs two
three-literal products and phase bit 1 is `!s6 | !s2`, where `s6` is
the executed `3ED` row-0 bit 0 at visit 46. Frozen before a fifth
payload pair and new R1 offsets 24/88, the gates predict all 64/64
receive decisions in each of four real-PROM Tx→line→Rx runs, including
new state `6C`. Each run recovers eight exact line bytes and the
aligned modeled 8251/8031 decodes the exact eight source bytes with
zero errors/overruns. The old six-bit table leaves all 64 decisions
unknown on each run; an independent reference is exact. This is one
unseen-state success under assumed ADC, latch, analog and serial
routes, not a physical C3 pass. Freeze the gates for gain/drift and
new-data tests, and test a photo-compatible row-latch/serializer path
to USART-01 without waiting for continuity measurements.
The [frozen row-0 gain challenge](g2/JOINT-MASK04-12A-ROW0-GAIN-CHALLENGE.md)
supplies new payloads at offset 24 and 75/100/125% of the fixed
line gain. The real-PROM reference line is exact in all six cases.
The frozen two-output gate recovers all decisions, eight line bytes
and exact aligned modeled 8251/8031 payloads at 100% and 125%, but
at 75% it makes 14 call and 10 answer payload-dibit errors. Every
error touches an unseen state; its phase for new state `52` is 2,
while the post-hoc graph requires 3. The feature's expanded 20-state
graph remains connected and conflict-free, but these low-level labels
are now development evidence: any revised gates require untouched
data/gain validation. Test a photo-compatible level or carrier-state
signal and the actual row-latch/serial route. C3/G2 stay open; missing
net continuity is not a blocker.
The [20-state row-gate holdout](g2/JOINT-MASK04-12A-ROW0-TWENTY-STATE.md)
now treats those six gain runs as development. Its connected phase
graph has 20 observed states and zero conflicts. One extra two-literal
term in phase bit 0 repairs state `52`; phase bit 1 is unchanged.
Frozen before a seventh payload pair, the revised gates recover 64/64
receive decisions and eight exact line bytes in all six real-PROM
Tx→line→Rx runs at R1 offset 88 and 75/100/125% level. Aligned modeled
8251/8031 handoff returns each exact eight-byte source payload with
zero errors/overruns; early and late SYNDET controls fail. The
independent reference is exact. All holdout states are among the 20
development states, so unseen-state and carrier-drift robustness
remain open. Test those with the gates frozen and a photo-compatible
row latch/serializer route; retain C3/G2 as active, not blocked.
The [offset-112 fresh-payload challenge](g2/JOINT-MASK04-12A-ROW0-PHASE112.md)
now supplies an unseen-state control on the real-PROM Tx→line→Rx path.
At fixed 100% level, the independent reference misses 2/64 call and
1/64 answer decisions; the frozen row gates miss 12/64 and 9/64,
respectively. The gate errors do not coincide with those reference
errors. Both selectors reach new states `12` and `5E`; the combined
22-state phase graph has zero conflicts and keeps every development
label, but the frozen gates assign `5E` phase 1 where the graph requires
0. Every gate error touches `5E`. Treat the offset-112 labels as
development if revising the gates, then test the revision on untouched
payloads and another carrier start. Also find a line fixture whose
independent decoder is exact at that start. These conditional failures
are next experiments, not a G2 blocker or a C3 pass.
The [22-state revision and fresh holdout](g2/JOINT-MASK04-12A-ROW0-TWENTYTWO-HOLDOUT.md)
move those failed offset-112 cases to development, fix the `5E`
phase under a connected zero-conflict graph, and choose +5 sample
alignment from a fixed-gain screen whose +4/+5 candidates are exact
on both development payloads. Frozen before a new payload pair at
offset 112, the revised gates give 0/64 wrong decisions and exact
aligned modeled 8251/8031 source bytes in both selectors. The
independent reference has 0 call and 2 answer errors, so its separate
decoder is not an absolute line oracle. All holdout states were in the
22-state development set. Test the frozen gates on another phase/level
that reaches new states and constrain the row capture and USART
hardware; these successes remain conditional C3 evidence, not a
physical pass or a goal blocker.
The [phase-120 new-state holdout](g2/JOINT-MASK04-12A-ROW0-PHASE120.md)
now freezes that 22-state gate and +5 line shift before another fresh
payload pair and carrier start. Both real-PROM Tx→line→Rx runs give
0/64 reference errors, 0/64 gate errors, exact offered line bytes and
exact aligned modeled 8251/8031 source bytes. They visit new state
`59` on 40/65 call and 42/65 answer symbols; the frozen gates assign
its anchored phase 2 correctly and all transitions extend the old
graph without conflict. This is one unseen-state success for a
conditional external consumer, not an executed DSC decision or traced
USART route. Next test a photo-compatible row-capture/serializer and
an independent output constraint while leaving C3/G2 active.
Make that route the next bounded C3 experiment. Start from the photographed
ADC0800 input candidate and four-bit U12 as one possible capture stage; assign
the remaining capture storage explicitly and label all untraced data and clock
connections as assumptions. In a real-PROM, controller-fed receive run,
capture `3ED` row-0 bit 0 at visit 46 and the two `3F8` Y snapshots at visits
46 and 93; hold their needed bits until the 20-state gates can combine them.
Test row-0-qualified capture against an every-row latch control, and test an
aligned RxC/SYNDET schedule against one-bit-early and one-bit-late controls
while serializing the recovered dibits to modeled USART-01 RxD. Compare the
resulting octets and 8031 state with the known source stream. If a latch or
timing variant fails, change that specific assumption or input condition and
run the next variant. These are circuit hypotheses, even when they produce
exact payloads; C3 passes only when the ADC and USART route is independently
constrained as required in [PLAN-2.md](PLAN-2.md#goal-g2).
The [row-capture/serial timing replay](g2/JOINT-MASK04-12A-ROW0-SERIAL-TIMING.md)
now applies that schedule to the six saved real-PROM holdout traces. At the
assumed 6,000-cycle RxC edge, the second `3F8` capture has 2,961 cycles of
setup; all six streams yield exact line and 8031-decoded source bytes. The
row-0 bit tolerates a one-visit-late capture, but a row-3 substitution or a
one-visit-late first or second Y makes 6–25 decision errors per stream. An
RxC edge before the second Y leaves 64 first-bit edges unavailable. The
replay narrows capture timing under labelled storage/clock/serial wiring; it
does not trace those pins or pass C3. Next capture all four `3ED` rows in a
real-PROM run and compare an every-row latch clock with row-0 qualification.
The [four-row real-PROM captures](g2/JOINT-MASK04-12A-ALL-ROW-LATCH.md)
now test both fresh call and answer payloads at offset 88 and 75% gain.
Their new Tx, PCM and Rx digests match the prior holdout. Row 0 gives 0/64
decision errors in each; rows 1 and 2 are zero at all 520 captured
symbol/visit positions and give 20/64 and 21/64 errors; row 3 gives
14/64 and 19/64. An every-row latch would finish on row 3, so this
proposed readout requires a row-qualified clock or another hold path.
Test an independently changed carrier/gain fixture, then constrain the
qualifier and storage from the photos. Keep C3/G2 active under labelled
wiring assumptions.
The photographed U19 NAND near U12 and the
[raw-PROM `3ED` decode](g2/RECEIVER-MASK04-3ED-PROM-LATCH.md) offer a
concrete every-row clock source, but the same `3ED` word executes in all
four rows. Its PROM bits alone cannot distinguish row 0. Model U24's
pictured four-bit counter, or another explicit stateful index, as the
qualifier: test the pre- and post-increment phases and all four low-bit
decodes against the captured call/answer streams. Keep the counter-to-gate
and gate-to-U12 pins assumed until a photo or independent signal constraint
separates them. Do not wait for that trace to run the phase screen.
The [U24-style phase screen](g2/JOINT-MASK04-12A-ALL-ROW-LATCH.md)
now tests those eight counter-edge/decode combinations on both saved
real-PROM row captures. Only pre-increment `00` or post-increment `01`
selects row 0 and makes 0/64 errors in both streams; the other six
make 14–21 errors. This constrains the logical counter phase under the
assumed modulo-four clock but does not identify the U24 pins or reset.
Next compare a second counter/reset source or seek an independent output
constraint while continuing C2/C3/C4 experiments.
Keep C2/C3/G2 open. These untraced connections are explicit, runnable
assumptions, not a goal blocker.
The [saved-readout gap audit](g2/JOINT-MASK04-12A-READOUT-GAP-AUDIT.md)
shows why selecting among the three frozen capture pairs cannot repair
that handoff: no pair supplies a correct known dibit at call data
indices `8,14,29` or answer indices `10,12,13,17,31`; four of those
positions have all three pairs unknown. Capture another executed
feature such as `3F9`/`3FA` Y at these windows, train its rule on
independent legal streams, and retest the held-out loopback. Missing
photo continuity does not block that experiment or relax C3.
The [independent `3F9`/`3FA` feature screen](g2/RECEIVER-MASK04-3F9-3FA-FEATURE-SCREEN.md)
tests 36 small transition features on six legal rotated-carrier runs.
A frozen 16-key `3F9` Y4/Y5 rule at visits 46/93 fits 24/24 training
dibits and makes no known errors but 16 unknowns among 48 independent
holdout dibits. The [buffered-line gap test](g2/JOINT-MASK04-12A-3F9-GAP-TEST.md)
then reruns the ROM-sensitive DAC→ADC path with matching trace/PCM hashes;
the frozen rule makes 3 call and 7 answer errors, leaves 24 unknowns
in each mode, and rescues none of the previously unanswerable gaps.
Inspect ADC quantization and `3F9`/`3FA` keys at those gaps, then test
a photo-compatible gain/phase or multi-sample circuit on fresh data.
This result rejects only that fixed lookup under its declared fixture;
C3 and G2 remain open.
The [paired `3F9` key audit](g2/JOINT-MASK04-12A-3F9-KEY-AUDIT.md)
matches independent training and buffered-loopback traces, then shows
that 24/32 data symbols per selector use transition keys absent from
training. Familiar keys also give 3 call and 7 answer wrong labels;
answer gap 10 shares key `110` with training but has different full
`3F9` bytes and a different dibit. The two-bit projection aliases
distinct executed states. Test more `3F9` bits or short history on
independent gain/phase-varied carriers, freeze the rule, and challenge
fresh buffered payloads. Treat the line and output circuit as explicit
assumptions; do not block G2 or relax C3.
The [full-byte `3F9` screen](g2/RECEIVER-MASK04-3F9-FULLBYTE-SCREEN.md)
now tests that next diagnostic on real-PROM carriers. A current-symbol
full-byte pair abstains on 27/44 training and 34/44 independent holdout
dibits. Including the preceding symbol fits all 44 training dibits,
but misses 9/44 independent holdout dibits and 8/31 call plus 16/31
answer buffered data dibits. This rejects the selected nearest-vector
readout, not all differential consumers of `3F9`. Inspect the executed
`3F9` arithmetic/ROM operands and build a circuit-like temporal decision
before a fresh line/USART replay. C3 and G2 remain open.
The [cross-fixture ADC equivalence check](g2/RECEIVER-MASK04-3F9-ADC-EQUIVALENCE.md)
matches all 640 saved `3F9`/`3FA` Y bytes at visits 46/93 to the prior
executed codebook of the **current ADC high nibble**, across 320 samples
and ten PROM traces. Every nibble occurs; `9` and `D` collapse to the
same `31/20` pair. Fixed-pair Y decoding is therefore an external
sample-processing hypothesis under these fixtures, not evidence of an
onboard recovered-bit output. Trace post-`3F9` Q/RAM history and a
later/mode-qualified consumer next. Keep C3/G2 active and the physical
connections explicit assumptions.
The [matched post-visit state replay](g2/RECEIVER-MASK04-POSTVISIT-STATE-HISTORY.md)
checks two legal 192,047-word mask-04 traces at identical exact ADC bytes
and sample positions with different preceding ADC bytes. In 8/21
eligible groups, R13 differs after `3F9` while its ROM address, Y and Q
agree. Executed `3FA` `55/C5` overwrites R13 to the same value; post-`3FA`
Q/RAM/Y and post-`3FE` Q/RAM/Y agree in all 21 groups. The direct-mode
history difference is transient and not visible at the tested Y/Q sites.
Try a photo-compatible mode or RAM-return route that consumes it before
overwrite, with matched-input controls. C3/G2 stay open.
The [held-mode `3FA` arithmetic test](g2/RECEIVER-MASK04-3FA-MODE-ARITHMETIC.md)
checks all 36,000 `3FA` words on two legal carriers with candidate held
`3EB` bytes `01`, `81`, and `A1`. The mapped `55/C5` calculation reads
R10 and D=`01`, writes R13 high, and leaves Q unchanged; old R13 is not
an operand. Held `81` changes pre-R13 on 10,827/12,000 paired visits
but never changes `3FA` Y or post-R13. Held `A1` changes Y/post-R13 on
all 12,000 paired visits through R10, yet matched ADC/phase groups show
no within-mode Y or Q history variation. Try another photo-compatible
return/mux timing that puts stored state on A or D before overwrite;
keep C3/C4/G2 open and the `3EB` frame route assumed.
The [legal-carrier delayed MCM93422 return](g2/RECEIVER-MASK04-LEGAL-RAM-RETURN.md)
now tests `3F9` Y-high → sample-paced RAM → offset-3 `3FA` D-high on two
192,047-word PROM receive runs with previous-carry TEST. Read-only and
write-only controls give identical `3FA` Y, but combined feedback
changes 5,859/6,000 visits per carrier, starting at visit 141. Among
21 matched exact-ADC/phase groups, only feedback gives history-sensitive
`3FA` Y in nine groups. This is a conditional consumed-memory path, not
yet a decoded dibit or echo residual. Freeze a circuit-like temporal
decision on independent carriers, challenge fresh buffered data, and
retain own/remote/mixed controls for C4. Keep all RAM/TEST/output wiring
assumed and C3/C4/G2 open.
The [legal-carrier delay equation](g2/RECEIVER-MASK04-RAM-RETURN-DELAY-EQUATION.md)
now hash-matches both high-return PROM runs and shows that all 12,000
`3FA` Y high nibbles equal the `3F9` high nibble from exactly three held
ADC samples earlier plus `0x20` modulo the high nibble; the first 141
visits retain the initialized `20`. Thus the history-sensitive high
output is a fixed delayed sample recoding under this fixture, not an
adaptive residual or recovered dibit. Test its low bit separately,
and seek a mode/return route with a varying trained operand or an
independently constrained receive/USART output. C3/C4/G2 remain open.
The [full-byte RAM-return equation](g2/RECEIVER-MASK04-RAM-RETURN-FULL-EQUATION.md)
now checks the remaining low bit against the same-input write-only
control and the independently executed `3FA` ADC codebook. All 12,000
feedback Y bytes equal the delayed `3F9` high code plus a bit that is
one exactly for current ADC high nibbles `6`, `B`, `C`; feedback never
changes that low bit. This fully explains the tested `3FA` output as
fixed delayed/current sample recoding, not a demonstrated onboard
dibit decision or adaptive residual. Pursue a consumed trained operand
or distinct output/USART route; C3/C4/G2 stay open.
The [held-`A1` `3FC` RAM-return challenge](g2/JOINT-MASK04-A1-RAM-3FC-ECHO.md)
combines a photo-compatible controller-frame mode input with delayed
external memory on the same real-PROM receive loop. All eight
own/remote/mixed/zero and write-only/return runs sustain, but the
`3FD` own-echo-versus-zero code contrast rises from 4.97 early to 5.97
late, and mixed-minus-remote rises from 7.48 to 8.48. All 46 latch
phases show the same non-attenuating result. Held `A1` changes output
scale relative to the prior `01` fixture but does not establish a
trained coefficient or C4. The [full arithmetic audit](g2/JOINT-MASK04-A1-3FC-ARITHMETIC.md)
checks 24,000 visits each at `3FC` and `3FD`: `A1` fixes pre-`3FC`
R10 at `20` (versus `10` in mode `01`), pre-`3FD` R5 at `00`, and both
carry inputs at `0`/`1`. The return is recoded through a different ROM
address, not combined with a varying consumed coefficient. Test a
distinct photo-compatible return/output route or a controller mode
transition with an identified trained operand; the
untraced mode and RAM wires remain hypotheses, not blockers.
The [joint-map phase-accumulator replay](g2/JOINT-MASK04-TX-PHASE-ACCUMULATOR.md)
now verifies R1 += D127 (mod 256) on 54,053 consecutive updates per
controller selector, and Y7 = R1 bit 7 at all 216,216 executed loop
words per selector. The first 18 continuous call/answer A4 dibits give
their exact cumulative quadrant steps. The assumed 9,600 Hz sample
clock turns `88` into 2,100 Hz and `B0` into a magnitude-1,800 Hz
carrier. This identifies an executed candidate digital modulation
mechanism; the D127 pulse decoder and physical DAC/line route remain
open C2 hypotheses, not goal blockers.
The [full-A4 pulse ablation](g2/JOINT-MASK04-TX-PHASE-PULSE-ABLATION.md)
extends those checks through all 32 controller-derived data dibits in
both modes. Each 384,256-word real-PROM run checks 96,053 consecutive
R1 additions and 384,216 Y7/R1-high relations. Replacing only dibit
23's four-visit `90` pulse with baseline `B0` leaves earlier symbol-end
phases equal and shifts that and every later symbol end by exactly
128/256, the predicted half-turn. This is causal internal transmitter
evidence under an assumed D127 input route; constrain the input decoder,
latch and DAC/line path before passing C2.
The [causal serial-edge pulse screen](g2/JOINT-MASK04-SERIAL-EDGE-PULSE.md)
now pairs the controller's actual 2,400-bit/s line bits and starts a
16-microcycle D127 pulse on each pair's second bit edge, rather than
offering the completed dibit at symbol start. Both full real-PROM
transmitter runs complete, but the fixed receive alignment makes
5/62 call and 3/62 answer reference errors; the best of eight sample
shifts still has 2/62 each. This rules out only that immediate-edge
pulse/analog fixture. Test a buffered symbol-boundary decoder or a
different photo-compatible pulse timing without treating the untraced
input logic as a blocker.
The [one-symbol buffered serial handoff](g2/JOINT-MASK04-BUFFERED-SERIAL-HANDOFF.md)
now tests that next decoder with the controller's actual paired TxD bits.
Both full real-PROM transmitter and receiver runs preserve the training
prefix, and the previously frozen 46/93 readout recovers all 32 data dibits
and eight line bytes per selector. With the data window shifted from bit 64
to 66, only aligned assumed SYNDET drives the paced 8251/8031 from `AF` to
`B0`; early, late, absent-window and opposite-selector controls stay at
`AF`. This is a causal, conditional zero-run route, not a physical C2/C3
pass: the paired-bit buffer, pulse gate, converters, decision circuit and
sync source are untraced. Keep G2 active and C2/C3 open; test those paths
under photo-compatible alternatives and new timing/data fixtures. The
frozen margin selector makes one call error here, so use the exact 46/93
result only for its stated fixture rather than assuming readout robustness.
The [buffered TxD-bit intervention](g2/JOINT-MASK04-BUFFERED-TXD-BIT-ABLATION.md)
now checks the candidate input link causally. The R1 recurrence
reconstructs all 846 executed Y7 samples in four saved buffered
real-PROM streams. Flipping controller TxD bit 40 in a controlled
counterfactual changes only four D127 visits at the next symbol
boundary and predicts a −90° phase step; two fresh 1,269,256-word
PROM runs first change Y7 at sample 744 and match the recurrence on
all 846 samples. This narrows the buffered pulse timing under its
explicit circuit assumption. Constrain the pair latch, D127 gate and
Y7/DAC path independently before passing C2; missing pin continuity
is not a G2 blocker.
The [non-zero buffered-payload challenge](g2/JOINT-MASK04-BUFFERED-PAYLOAD-CHALLENGE.md)
keeps the same frozen 46/93 rule and real-PROM Tx/Rx runs but changes the
eight line bytes twice. Both selectors recover all 32 data dibits and the
exact bytes with zero errors/unknowns; the answer stream covers all 16
adjacent-dibit transitions. This weakens the zero-payload overfit concern,
but the paired-bit buffer, DAC/ADC and USART output circuits remain
unidentified. Challenge gain and sample phase next, and seek the actual
photo-compatible pulse/readout routes. Keep C2/C3 open and G2 active.
The [one-sample buffered phase challenge](g2/JOINT-MASK04-BUFFERED-SAMPLE-PHASE.md)
hash-matches the saved real-PROM transmitter source before shifting the
candidate ADC waveform and running four new real-PROM receiver traces.
One sample early leaves frozen 46/93 exact for both varied payloads;
one sample late leaves four call and three answer dibits unknown, with no
wrong decisions. The previously frozen margin selector resolves those
unknowns on these streams, but it failed once on the nominal zero-run.
Treat both readouts as timing-dependent diagnostics and test a physically
plausible sample/decision circuit with gain and phase controls. Neither
the untraced clock nor this narrow abstention is a G2 blocker.
The [buffered full-DAC-bus screen](g2/JOINT-MASK04-BUFFERED-DAC-BUS.md)
tests the 12 previously frozen Q4→B5-compatible byte orders against actual
`127` and `129` Y bytes from both complete real-PROM transmitter runs.
Six orders at either latch word produce the modeled 2,100 Hz A1 tone,
quiet gated A2 interval and 0/64 A3/A4 differential errors per selector;
the other six miss one call symbol. The two latch words produce distinct
byte streams, yet these decisions do not distinguish them. Carry the six
full-byte routes as explicit C2 candidates and seek a second DAC pin or
sample-clock/output-node constraint; do not promote the assumed bus, gate
or filter to verified physical wiring. Keep C2 open and G2 active.
The [full-byte buffered Tx→Rx→8031 replay](g2/JOINT-MASK04-BUFFERED-FULL-BUS-LOOPBACK.md)
now takes the previously frozen top-correlation Q4→B5-compatible DAC order
through real-PROM transmit and receive runs at both candidate latch words.
The independent decoder is exact; the frozen 46/93 readout makes no wrong
decisions but abstains on three call or five answer data dibits. A new
fixed-first fallback to the previously frozen margin selector fills those
abstentions and recovers all eight line bytes in the **same inspected
fixture**. Aligned assumed SYNDET reaches controller `B0`; early, late and
opposite-selector controls stay at `AF`. Freeze this fallback and test a
separate non-zero payload holdout before claiming generalization. The
DAC/ADC/decision/USART routes remain hypothetical, so C2/C3 stay open
and G2 active.
The [non-zero full-byte holdout](g2/JOINT-MASK04-FULL-BUS-PAYLOAD-HOLDOUT.md)
now freezes that bus and fixed-first readout on two eight-byte streams
recorded before the fallback was proposed. Both real-PROM Tx/Rx runs at
both candidate latch words recover all 32 data dibits and exact bytes;
the answer stream covers all 16 adjacent-dibit transitions. Fixed 46/93
abstains twice for call and nine times for answer, while the margin
selector's one answer error is overridden by a known fixed decision.
This strengthens the conditional full-byte Tx/Rx dataflow, but the
readout circuit, DAC/ADC wiring, clocks, analog line and USART path remain
unverified. Test gain/phase robustness and photo-compatible decision
hardware; C2/C3 stay open and G2 active.
The [full-byte ADC-level challenge](g2/JOINT-MASK04-FULL-BUS-LEVEL-CHALLENGE.md)
now keeps that frozen bus, latch and readout but scales the zero-run PCM
to 0.75 and adds ±16 counts. All four real-PROM receiver runs complete;
the independent decoder remains exact with no clipping, while the
fixed-first readout has 3–8 wrong and 3–9 unknown data dibits per case.
Thus the current rule does not generalize to these modest input-level
changes. Seek an executed or photo-compatible gain/midpoint/threshold
path and freeze its rule before a fresh payload/phase challenge. This
failed fixture narrows C3; it does not block G2 or erase the nominal
conditional dataflow.
The [preamble-calibrated AGC candidate](g2/JOINT-MASK04-FULL-BUS-AGC-CANDIDATE.md)
now fixes a target midpoint/RMS from the nominal call's first 128 A3
samples, estimates each altered stream's midpoint/RMS from only its own
first 128 A3 samples and corrects later samples. Under the same four
0.75-gain/±16 fixtures, all real-PROM receive runs recover the exact
eight line bytes with the unchanged frozen readout. This is a sufficient
**external analog-stage hypothesis** for those affine changes, not an
identified DSC AGC algorithm or photographed circuit. Freeze it for a
separate non-zero payload and phase/noise holdout; keep C3 and G2 active.
The [non-zero AGC holdout](g2/JOINT-MASK04-FULL-BUS-AGC-HOLDOUT.md)
now keeps that fixed target, 128-sample acquisition window, full-byte DAC
order and receive rule on two previously recorded non-zero streams. All
four 0.75-gain/±16 real-PROM Tx/Rx cases recover the exact eight bytes;
the answer stream covers all 16 adjacent-dibit transitions. This supports
the conditional AGC-plus-PROM dataflow over data and affine level changes,
but the AGC stage remains external and hypothetical. Test carrier phase,
noise and photo-compatible gain/decision circuits without treating those
untraced nets as a G2 blocker; C2/C3 stay open.
The [full-byte carrier-offset challenge](g2/JOINT-MASK04-FULL-BUS-CARRIER-OFFSET.md)
now shifts that modeled line by ±7 Hz while keeping the non-zero payloads,
AGC target, DAC bus and receive rule frozen. Zero-offset controls reproduce
the saved PCM; the independent decoder is exact in all six real-PROM receive
runs. The fixed 46/93 rule makes no wrong data decisions but abstains on
2–9; its frozen margin fallback recovers exact bytes only at zero offset
and answer −7 Hz. Call ±7 Hz and answer +7 Hz fail. Seek a phase-aware
capture/decision route and test it on fresh inputs after freezing it.
This narrows the current external readout, not the DSC's possible tracking
function; keep C2/C3 open and G2 active.
The [adjacent-visit screen](g2/JOINT-MASK04-FULL-BUS-OFFSET-VISIT-SCREEN.md)
reruns those six unchanged PROM inputs while reading eight pairs of executed
Y bytes. All prior ADC and PROM hashes match. Across the three failing
offset cases, four fixed-rule gaps have no correct known answer from any
tested pair. Thus choosing a different pair among these visits cannot by
itself repair the frozen two-feature readout. Inspect those Y states and
test a different phase-aware or multi-sample decision on a fresh fixture;
do not treat this narrow pair-family failure as a G2 blocker or C3 pass.
The [gap-byte audit](g2/JOINT-MASK04-FULL-BUS-OFFSET-GAP-AUDIT.md) now
captures ADC, `3F8` Y and `3ED` row bytes at all four gaps in hash-matched
real-PROM runs. Two adjacent-pair gaps contain a primary/alternative
decision conflict (`0` versus the correct `2`); the two symbol-56 gaps
have no correct known consensus among eight tested pairs. Executed Y
bytes vary with the input, so test a new phase-aware row/multi-sample
feature and freeze conflict handling before a fresh payload/phase holdout.
The currently untraced decoder path keeps C3 open, not G2 blocked.
The [frozen row-logic transfer test](g2/JOINT-MASK04-FULL-BUS-ROW-LOGIC-OFFSET.md)
now applies the earlier phase-47 Boolean decoder to all six full-byte
carrier-offset PROM runs. The traces and ADC hashes match the offset
challenge, but that external gate misses 96/192 data dibits at its frozen
visit, including 18/32 and 20/32 in the two zero-offset controls. Two
correct gap snapshots were not representative. Capture complete full-byte
row-byte sequences for a new causal development/holdout readout, or test
another photo-compatible ADC/latch route; C3 remains open and G2 active.
The [complete full-byte receive-state corpus](g2/JOINT-MASK04-FULL-BUS-RECEIVE-STATES.md)
now retains `3F8` and `3ED` Y bytes at ten visits for all 65 symbols in
each of the six hash-matched real-PROM runs. A bounded transfer test fits
two existing four-bit transition readouts on only the zero-offset call
and answer streams. The `47/94` table has no training conflicts but
recognizes only 26/128 shifted data dibits; `46/93` recognizes 38/128
and gets one wrong. Do not fit a new rule to these already inspected
offset cases and call them a blind holdout. Use the corpus to specify
a causal multi-sample hypothesis, then challenge it with new payloads
and phase starts; C3 remains open and G2 active.
The [sampled-byte identity audit](g2/JOINT-MASK04-FULL-BUS-ADC-ROW-IDENTITY.md)
now gives a stronger interpretation of those Y captures: all 3,900
sampled `3F8` Y bytes equal `(ADC & F0) | 0F`. At 1,170 sample boundaries,
`3ED` row-0 Y is an observed one-input codebook of the preceding ADC
high nibble, and row-3 Y of the current nibble, with no contradictions
across six streams. The direct `3F8` and two-row readouts therefore
carry quantized input samples, not independent evidence that DSC made
a dibit decision. Seek a downstream retained-state/output consumer
and a USART bit route; do not promote external sample slicers to C3.
The [mask-04 receive impulse test](g2/JOINT-MASK04-RECEIVE-IMPULSE-MEMORY.md)
now changes one ADC sample on a constant stream and on a varying
reference waveform, with common tails and low-nibble controls. Six
96,047-instruction PROM runs share the same PC path. High-nibble changes
affect `3F8`/`3F9`/`3FA` Y and Q/R1 (plus R12 on the varying stream)
for exactly the 47 held visits, then all captured channels reconverge
on the first restored-input visit. Low-nibble changes leave captured
state and executor trace digests identical. This four-row `D3EB=01`
fixture shows no persistent post-visit difference at the captured sites;
try a labelled mode-qualified
or external-RAM feedback route
with matched-prefix/common-tail controls. C3/C4 remain open, G2 active.
The [full-word pulse trace](g2/JOINT-MASK04-RECEIVE-PULSE-CARRYOVER.md)
corrects that broad wording: the selected capture points rejoin, but
14 ALU results, six Q rows and four ROM reads differ during the 21
microinstructions before the next identical ADC byte reaches `3F8`.
The complete modeled state rejoins at the following `3FA` word.
Search for a photo-compatible consumer of this short previous-sample
window; it is not itself a received-bit decision or C3 pass.
The [U19/U12 carryover replay](g2/JOINT-MASK04-CARRYOVER-LATCH-PULSE.md)
now tests one such consumer against the same matched-tail pulse. The
raw-PROM `3ED` gate gives 12,000 edges per run; an assumed row-0-only
U12 clock holds prior Y's low nibble as `0/5` at the first restored
visit's row-3 edge, where live Y[2:0] is `2/2`. The unqualified
every-row latch holds zero. This supplies a conditional previous/current
sample pair after the DSC state rejoins, but the earlier 45° U12
decoder fails, so C3 still needs a phase-robust consumer and USART path.
The [post-visit Q/RAM codebook](g2/JOINT-MASK04-POSTVISIT-STATE-CODEBOOK.md)
now compares 9,000 receive visits across three different dibit streams.
At row-3 `3FE`, each of the sixteen observed ADC high nibbles maps to one
Q/RAM state across all three runs (nine distinct states total). This
capture point supplies no additional phase history in the tested direct
`D3EB=01` fixture, though the short carryover and assumed U12 latch remain.
The [U12 code-collision replay](g2/JOINT-MASK04-U12-CODE-COLLISION.md)
now checks the prerequisite for a phase tracker using a controlled `1F`
versus `6F` sample-25 pulse. Executed `3F8`, `3F9` and `3FA` Y differ
on all 47 affected visits, but all 3,000 assumed U12 row-pair captures,
`3ED` Y, Q and post-visit RAM agree. The candidate U12-only stream loses
this input distinction; a longer history of that same stream cannot
recover it. The artificial pulses are not a legal dibit challenge, so
do not infer that all modem data are lost.
The [executed `3F9`/`3FA` codebook](g2/JOINT-MASK04-RECEIVE-3F9-3FA-CODEBOOK.md)
tests that route on three legal streams at 0°, 45° and 90°. Each site
executes once per ADC visit, while `3ED` executes four times. Across
9,000 visits, `3F9` has 15 values and `3FA` only `20/21`; both are
single-valued by the current ADC high nibble over 110 observed adjacent
sample pairs. Thus these Y taps expose current-sample recodings in this
fixture, not an observed received-bit decision or carrier-history state.
The [32-word receive history scan](g2/JOINT-MASK04-RECEIVE-HISTORY-SCAN.md)
now tests that question on five legal rotated-payload runs and 131
observed adjacent ADC-nibble pairs. Across 14,990 complete visits,
Y and Q at every offset depend only on the currently selected nibble.
Only R12/R13 at `3F8` and R13 at `3F9` retain previous-nibble
dependence; RAM rejoins at `3FA`. The earlier transient Y/Q carryover
occurs before the next `3F8` selection, not after it. Next challenge a
photo-compatible latch on that preselection interval with legal symbol
transitions and rotated phases, or change the assumed mode/feedback and
repeat the history scan. Follow any candidate bit to controller/USART
RxD. The direct `3F8` Y nibble merely copies quantized ADC data. Keep
candidate wiring labelled, C3 open and G2 active.
The [held controller-mode impulse](g2/JOINT-MASK04-RECEIVE-MODE-IMPULSE.md)
now repeats the varying-waveform pulse under candidate `3EB` D bytes
`01`, `81` and `A1`. Nine real-PROM runs complete the same PC path;
the `01` controls hash-match the prior experiment. Each high-nibble
pulse changes intermediate Y/Q/R1 for only its 47 held visits, with
zero captured differences after input rejoins. Low-nibble controls
leave captured state and executor trace digests unchanged. The observed
controller bytes do not create memory on this direct lane in the tested
mode, so try a photo-compatible external-RAM, mode-gated or alternate
input/output route rather than treating this as a C3/C4 pass or blocker.
The [photo-B5 Y7 route test](g2/JOINT-MASK04-PHOTO-B5-Y7-ROUTE.md)
reassigns the same executed Y7 samples to a different candidate latch
input: Y7→LS273 D4, then the photo-suggested Q4→DAC08 B5 segment.
At B5's eight-count weight, both call/answer streams retain 2,100 Hz
tone, A3 half-turns and 0/62 filtered A3/A4 errors after an assumed
A2 gate and Q=1 line stage. This is a photo-compatible alternative to
the Y7→B1/MSB bus family, not independent waveform evidence or a C2
pass. Test Y7→D4 and the analog output route next.
The [adjacent D4-track screen](g2/JOINT-MASK04-PHOTO-B5-Y7-ROUTE.md#adjacent-d4-track-and-b6-sensitivity)
adds a tentative D4→DAC08 B6 segment: the front track runs toward that
pad region, but its endpoint is obscured. If Y7 occupies both B5 and B6
at the sample edge, the executed-stream replay still gives 2,100 Hz and
0/62 filtered errors per selector. Treat this as gain sensitivity, not
net verification; resolve the D4 source/adjacent pad timing while continuing
other runnable C2/C3 tests.
The [long controller-timed A2 replay](g2/JOINT-MASK04-A2-LE-TIMED.md#photo-suggested-b5-path-under-the-same-controller-hold)
now combines that photo-suggested B5 segment with the executed 8031
frame-hold duration in two uninterrupted 2,040,256-word mask-`04`
PROM runs. All 24 B5/B5+B6 weight, latch-phase and gate-release cases
have a 2,100 Hz candidate tone, quiet modeled A2 and 0/62 A3/A4
filtered errors. Y7 samples match across the two raw-PROM latch phases.
This is a stronger conditional C2 timing candidate, but Y7→D4,
CD4094→74LS373, DAC current output and line wiring remain untraced;
keep C2 open while testing those photo-compatible routes.
The [latch-phase sweep](g2/JOINT-MASK04-LATCH-PHASE-SWEEP.md) anchors its
zero-offset recurrence to all 832 Y7 samples in each complete call/answer
PROM run, then projects all 375 possible sample-clock visit offsets. All
retain a 2,100 Hz tone peak; 328/375 per selector retain 0/62 filtered
data errors and the other 47 each miss one decision at the same index.
This makes the carrier candidate robust to loop-visit clock phase while
leaving the exact latch edge and receiver alignment unresolved. Do not
promote this projected phase sweep to a traced C2 output route.
The [executed Tx→Rx loopback](g2/JOINT-MASK04-TX-RX-LOOPBACK.md) now
feeds each saved controller-derived real-PROM Y7 stream through the
declared B5, A2-gate, analog-filter and complementary-ADC fixture into
a separate 756,047-instruction real-PROM receive run. Both selectors
yield 0 wrong and 0 unknown among 62 measurable A3/A4 dibits with the
frozen readout; the opposite-selector control gives ten wrong data
dibits. This links the candidate transmitter and receiver behaviors,
but the physical bridge, decision circuit, final A4 dibit and USART
handoff remain open. Extend the transmitter capture for the six samples
lost to alignment, then test the complete line-byte handoff.
The [full zero-run handoff](g2/JOINT-MASK04-FULL-ZERO-HANDOFF.md) now does
that extension with 1,257,256-instruction transmitter and 768,047-word
receiver runs per selector. The already frozen 46/93 receive pair
recovers all 32 data dibits and the exact eight 8031-scrambled line
bytes for both call and answer; the paced controller reaches `AF→B0`
only with the aligned bit-64 SYNDET pulse. The ADC-margin selector
instead makes one call-side error at symbol 44 by preferring a later,
larger-magnitude but wrong pair. Keep that failure visible: it rejects
ADC margin alone as a general selector for this joined waveform, while
the successful fixed pair remains a conditional external readout.
Continue testing the phase/decision source and physical serial route;
the modeled analog and inter-board links do not close C2 or C3.
The [complementary DAC-output test](g2/JOINT-MASK04-DAC-OUTPUT-POLARITY.md)
inverts the hash-matched full-stream B5/filter PCM as a pin-2 versus
pin-4 current-output hypothesis. New real-PROM receive runs keep 0/63
errors and recover the same eight line bytes per selector under the
frozen 46/93 readout. The board output polarity and downstream analog
path remain unresolved, but polarity alone does not distinguish the
candidate digital handoff in this fixture.
The [joined gain/bias challenge](g2/JOINT-MASK04-FULL-ZERO-ANALOG-VARIANTS.md)
hash-matches the reconstructed Y7 and nominal PCM to those executed
full-chain runs, then feeds four 0.75-gain, ±16-count PCM variants into
new real-PROM receive executions. The independent reference decoder
remains error-free, but frozen 46/93 leaves 14–19 data dibits unknown
and up to three wrong; the margin selector also fails. Do not generalize
the nominal controller handoff to altered input levels. Seek an executed
gain/midpoint or adaptive decision state and test it on fresh fixtures;
continue C2/C4 work in parallel with this open C3 question.
The [phase-47 state probe](g2/JOINT-MASK04-RX-STATE-LEVEL-PROBE.md)
replays the exact nominal and +16-biased, 0.75-gain call receive traces
and records all modeled Am2901 RAM bytes and Q at each symbol. R0, R1,
R12 and Q differ on 24/64 symbols; the other 13 RAM bytes stay fixed at
this site, and R1 equals row-3 Y on every capture. The previously frozen
phase-47 Boolean readout makes 11/63 errors at each level on the joined
waveform. These results do not identify an AGC/decision state; inspect
other visits or an external latch path before proposing a new adaptive
rule, while keeping C3 active.
For C4, the [mask-04 external-RAM echo screen](g2/JOINT-MASK04-EXTERNAL-RAM-ECHO-SCREEN.md)
uses a sample-paced counter, write/freeze gate and three-sample low-nibble
readback with zero, own echo, independent remote and mixed controls.
The `3FA` low-nibble latch stores only the initial `01` byte. A `3F9`
low-nibble latch stores changing bytes and alters the PROM trace without
loop exit. Correcting the four-row address-clock and write-gate counts
shows delayed `3FA` changes in the common zero tail, but the late
mixed-minus-remote `Y3FA` code difference grows from 0.439 to 6.065
instead of attenuating. The [matched-tail RAM pulse](g2/JOINT-MASK04-RAM-PULSE-FREEZE.md)
isolates one changed byte and a delayed `3FA` response at either three
or sixteen samples. These establish a conditional memory route, not
echo cancellation. Test another photo-compatible output or mode-qualified
return under the same controls; keep C4 and G2 active.
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
The [Timer 1 follow-up](g2/RECEIVER-TIMER1-OFFSET-HANDOFF.md) enables
the existing 8031 timer model during that paced handoff. Both delay
cases execute 57 timer interrupts with no receive overrun or emulator
error; only the aligned SYNDET pulse reaches `B0`. This removes one
timing shortcut, but an unheld-RAM15 control drops to state `00`,
consumes no bytes and overruns seven characters in both delays. The
ROM shows why: Timer 1 decrements bank-2 `R5:R4` at RAM15:RAM14, and
the zero synthetic seed underflows the high byte. A one-time
ROM-literal `75:30` seed, with no per-dispatch force, survives all 57
interrupts and again reaches `B0` with eight exact bytes; the final
countdown is `74:F7`. This removes the continuously held gate from the
successful fixture. The [Timer-paced `AE→AF→B0` replay](g2/RECEIVER-AE-AF-ZERO-HANDOFF.md)
now starts at synthetic `AE` with the two ROM countdown literals. The
ROM decodes DTE byte `02` to mode `05`, reaches `AF` after 51 Timer 1
interrupts with RAM15:RAM14=`74:FD`, then consumes eight exact
PROM-derived receive bytes and reaches `B0` only with the aligned
external SYNDET pulse. Early, late, absent, opposite-selector and
wrong-mode controls do not reach `B0`. This establishes the executed
`AE→AF` transition under the fixture, but the predecessor into `AE`,
countdown inheritance, sync source and physical serial route remain
assumptions. Test those paths with photo-compatible candidates; keep
C3 open and G2 active without waiting for a continuity measurement.
The [one-state-earlier replay](g2/RECEIVER-AD-AE-AF-ZERO-HANDOFF.md) now
starts at synthetic `AD` with only the `75:30` long countdown seeded.
The ROM advances `AD→AE` when RAM64 reaches eight, loads the `AE` short
timer itself, then reaches `AF→B0` on the same aligned receive stream;
the early, late, absent, opposite-selector and wrong-mode controls do
not reach `B0`. This narrows the remaining initialization assumption to
the entry into `AD` and its inherited long countdown. Test that
predecessor and a photo-compatible sync/serial route while C3 stays open.

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
means this is not a physical SYNDET timing measurement. The first port-01
write is local transmit traffic; its time does not identify the first
arriving remote bit. Keep the frame decoder as a conditional candidate
until a receive-side timing relationship is shown. Compare it with no
pulse, an unqualified bit-5 rise and pulses one bit or one byte away;
if it misses the controller signature, revise the route. The
[first-non-`11` SYNDET screen](g2/RECEIVER-SYNDET-PREAMBLE-TRANSITION.md)
rules out a simpler data-dependent trigger: for both controller
scrambler delays, 64/256 possible first payload octets keep dibit `11`
past the true data boundary, and a representative late pulse shifts the
paced USART byte. Seek a payload-independent receive boundary event or
photo-compatible sync connection; C3 and G2 remain active without waiting
for continuity.
The [nonzero frame-mode handoff](g2/RECEIVER-MASK04-NONZERO-FRAME-HANDOFF.md)
now challenges that boundary with first payload bytes `01` and `02`, whose
line streams keep `11` for one data dibit, plus `3D` and `5A`, whose
first line octet is an entire `FF` preamble-like byte. Four
768,047-instruction PROM runs recover 63/63 measurable dibits and all
eight line bytes; the paced
controller descrambles the exact payload only with the assumed bit-64
SYNDET placement. This strengthens the conditional receive path but does
not supply a physical sync source or close C3.
The [random eight-byte handoff](g2/RECEIVER-MASK04-RANDOM-PAYLOAD-HANDOFF.md)
now challenges the frozen readout with four complete nonzero payloads,
two per controller scrambler delay. Four 768,047-instruction PROM runs
recover all 252 measurable dibits and 32 line octets. With an aligned
assumed external SYNDET pulse, the paced 8251 and unchanged 8031 ROM
consume and descramble every payload; one-bit-early, one-bit-late and
opposite-selector controls fail. This strengthens the conditional C3
data path but leaves the capture/serializer, RxD/RxC, frame edge and
SYNDET source untraced. Continue with photo-compatible route/timing
tests; do not promote the handoff to a physical C3 pass.
The [new-angle challenge](g2/RECEIVER-MASK04-RANDOM-ANGLE-CHALLENGE.md)
reuses those four payload seeds at 15° and 105° with the receive rule
frozen. Four more real-PROM runs recover all 252 measurable dibits and
32 line bytes. This widens the conditional result to new carrier angles,
but still leaves the external `3F8` consumer, frame edge and physical
USART/SYNDET path untraced. Keep C3 open and try a photo-compatible
latch/serializer route; missing net continuity is not a blocker.
The [±7 Hz payload handoff](g2/RECEIVER-MASK04-OFFSET-PAYLOAD-HANDOFF.md)
keeps the ADC-margin selector frozen and runs two fresh complete
eight-byte streams through the real PROM and paced 8251/8031 model.
All 126 measurable dibits and 16 line bytes recover, and the ROM
descrambles both payloads only with aligned assumed SYNDET and the
matching selector. This tests carrier drift with new data, but the
margin-selection hardware, serial path and SYNDET source remain
unidentified. Keep C3 open and G2 active while testing plausible routes.
The [line-USART reinitialization screen](g2/RECEIVER-USART-REINIT-SCREEN.md)
instruments the Timer-1-paced real-ROM `AD→AE→AF→B0` fixture. Neither
selector writes line-side control port `05` before or during the eight
received bytes; the only five control writes program DTE port `06`.
This rules out a late 8031 line-USART reset in that executed path as the
source of byte alignment. An earlier setup, clock gating or external
SYNDET route remains possible; test those as labelled candidates.
The [held-SYNDET/RxC-gate screen](g2/RECEIVER-RXC-GATE-SCREEN.md)
tests another photo-compatible timing family: assert external SYNDET
before the segment and withhold RxC until the first data bit. For all
six saved PROM-derived streams, opening RxC at bit 64 exactly matches
the earlier pulse handoff; opening at bit 0, 63, 65 or never does not
deliver the complete intended stream. Seek a receive-side event that
can open the clock at that boundary, while keeping both gate and pulse
routes conditional and C3 open.

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
The [extra-capture-bit screen](g2/RECEIVER-MASK04-EXTRA-CAPTURE-BIT-SCREEN.md)
tests Y4 or Y5 from either visit as a fifth bit on eight development
PROM traces, then scores a separate 13-angle seed. Every added bit
leaves more unknown decisions than the four-bit baseline (122–196
versus 84 of 611), and none gives a consistent quadratic transition
rule across the combined captures. This scopes out simple bit addition,
not the complementary dual-feature rule. The [explicit one-bit latch
replay](g2/RECEIVER-MASK04-3F8-TRANSIENT-BIT.md) now includes the startup
edge and holds Y7 through all four later `3ED` observations per complete
receive visit; its 32 symbol-visit row-3 observations agree with the
executed `3F8` Y7. The [long zero-run latch handoff](g2/RECEIVER-MASK04-DUAL-ZERO-HANDOFF.md)
now clocks Y5–Y7 at every candidate gate edge and reads the held value
at row-3 `3ED` for visits 47 and 94 in two 768,047-word PROM streams.
Both recover the controller line bytes, but a preceding-visit row-0
capture control also succeeds, so those fixtures do not fix the symbol
clock phase. The [boundary-impulse replay](g2/RECEIVER-MASK04-CAPTURE-PHASE-BOUNDARY.md)
now separates them: one-visit ADC bit-7 flips at 47/94 make only the
row-3 readout abstain (13/31), while flips at 46/93 make only row 0
abstain (11/31). Both decode the unmodified stream, so the diagnostic
does not identify the physical phase. Constrain the symbol clock from
photo-compatible dividers or another natural phase-sensitive stimulus,
then test the two-visit consumer and RxD/RxC route; keep C3 open and G2 active.
The [sample-clock phase replay](g2/RECEIVER-MASK04-SAMPLE-CLOCK-PHASE.md)
tests the photographed 14.4 MHz oscillator against all 6,000 executed
receive visits. With one microinstruction per oscillator period and a
9,600 Hz sample clock, only offsets −3, −2 and −1 microcycles from the
first `3F8→3F9` latch edge match the 47/46-visit input schedule without
a same-cycle race. A 2,400 Hz RxC edge at sample index 3 leaves
1,478–1,480 cycles after the second capture; index 2 is 20–22 cycles
too early. This constrains a runnable clock hypothesis, not the traced
divider or physical phase. Test the oscillator/counter continuation and
the two-visit symbol consumer next; C3 remains open.
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
The [direct MSB phase replay](g2/JOINT-MASK04-MSB-SEGMENT1-PHASE.md) now
measures the raw candidate output bit in both executed controller-derived
PROM streams. At all four free-clock phases, adjacent A1 symbols hold a
steady 2,100 Hz phase while all 31 A3 symbol boundaries make 180°
reversals at 1,800 Hz. Full-byte captures differ by phase, but their
MSB streams are identical. This directly supports the segment-1 digital
output behavior under the Y7→latch→DAC08 B1 hypothesis; the physical
wire and analog line output remain open, so continue with a photo-compatible
route or independent analog constraint rather than calling C2 passed.
The [direct A4 data-phase replay](g2/JOINT-MASK04-MSB-DATA-PHASE.md)
now compares raw executed MSB symbol phasors with the controller's
32 segment-2 dibits. Both call and answer streams give 0/32 wrong
quadrant steps, including the A3→A4 boundary; the opposite phase sign
misses six and eight. The four free-clock phases have identical MSB
streams, so this is 64 distinct data comparisons. It ties the conditional
DSC output bit to the controller's actual data pattern without the assumed
analog filter, but the physical DAC and line route remain open. Continue
with photo-compatible output-route hypotheses; do not mark C2 passed.
The [fresh controller-payload replay](g2/JOINT-MASK04-FRESH-CONTROLLER-PAYLOAD.md)
now runs the preserved 8031 scrambler locally on nonzero call/answer
data bytes and feeds the new dibits through the same real-PROM transmit
candidate. Both 32-dibit streams give zero direct phase errors and zero
errors under the existing filtered reference receiver; opposite phase
sign and zero-data controls fail. The raw phase margin is narrow (worst
40.29° error against a 45° boundary), and the uninterrupted 8031 main
loop, DAC latch clock/data pins and analog line path remain unverified.
This strengthens the candidate `127–12A` data-modulator role but does
not pass C2. Continue with an independently constrained output route.

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
The [joint-map echo washout](g2/JOINT-UPPER-ECHO-WASHOUT.md) adds a
history control to the separate mask-`08` receive fixture: after 128
own-transmit-echo samples, all modeled Q/RAM and Y bytes reconverge
with a zero-input run within three ADC visits of a common zero tail.
This rejects retained internal tap state in that fixed fixture, not
the photographed external RAM or an untested train-enable path. Seek
the external tap-memory/mode route before extending the same fixed
echo window; keep C4 open and G2 active.
The [external-RAM bus screen](g2/JOINT-UPPER-RAM-BUS-SCREEN.md)
checks 2,048 executed receive visits under held and varying ADC input.
No reached Y site increments like an 8-bit RAM address, and no bare
PROM bit is active low at just one loop word; U18 D2/D4 pulse high at
`3EC` and U18 D7 at `3EA`. The DSC 3557 photo places a 74LS163 counter
and 74LS157 mux near four MCM93422 RAMs. Test an explicitly labelled
external counter/mux, inverted or decoded write strobe, data latch and
RAM-to-DSC return route. Start with a photo-compatible counter address,
one candidate latch/write edge and one RAM readback input; compare write
enabled, write disabled and no-feedback runs from the same initial RAM
contents and PROM input. Vary the plausible strobe polarity or latch edge
if the result depends on it. Record the assumed pins and timing, the RAM
state after training and whether a common zero tail preserves any echo
history. Proximity does not establish a net, but the missing net trace does
not defer this experiment or make C4 a goal blocker.
The [counter/RAM feedback screen](g2/JOINT-UPPER-RAM-FEEDBACK-SCREEN.md)
now runs that declared route and its controls. A `3FA` high-nibble return
first changes `3EB` D to `21` on a counter revisit and exits the fixed
receive loop after 258 ADC visits; a `3F9` high-nibble latch also exits.
Low-nibble return changes RAM but leaves the modeled Am2901 trace equal to
the no-feedback control over 768 visits. These reject only the tested
free-running write/read fixtures. Next try a photo-compatible training
write gate and freeze, then compare retained RAM and line residual across
own-echo, remote-only and zero-input runs. Keep C4 open and G2 active.
The [training/freeze screen](g2/JOINT-UPPER-RAM-FREEZE-SCREEN.md) closes
that assumed write gate after 256 loop visits. Its frozen RAM retains
different input histories. High-nibble feedback at `3EB` exits on one
prefix but changes 1,018/1,024 tail trace rows while staying in the loop
on another; low-nibble feedback at `3FA` changes 122/114 tail rows across
the two prefixes and leaves R13 changed for one. This is a conditional
stateful effect, not a demonstrated echo residual. The per-loop counter
spans only about 1.4 held ADC samples; next clock it once per sample and
compare controller-derived own echo, independent remote and zero-input
training with a frozen write gate and no-feedback control. Keep C4 open.
The [sample-clocked echo replay](g2/JOINT-UPPER-RAM-SAMPLE-CLOCK-ECHO.md)
now runs that comparison for 128 held ADC samples and a common 64-sample
zero tail. All 12 no-feedback/low-nibble PROM runs sustain 36,000 receive
visits. Frozen low-nibble RAM feedback changes `3FA` Y under own echo,
remote and even zero training; three- and 64-sample read offsets both
increase, rather than attenuate, the tested own-echo `3FA` Y difference
from a same-route zero run. Two high-nibble `3FA` return routes were also
run: the three-sample lag exits under all four inputs, while the
64-sample lag survives only zero input and exits under remote and both
own-echo inputs. Thus neither tested nibble/offset is a sustained,
selective echo path across these controls.
This is a negative result for that code-space proxy and wiring fixture,
not a measured line residual or a rejection of external echo RAM.
Try another photo-compatible RAM return/output or controller mode path
with the same own-echo, remote and zero controls; keep C4 open and G2
active without waiting for a pin-level trace.
The corrected [four-row RAM screen](g2/JOINT-MASK04-EXTERNAL-RAM-ECHO-SCREEN.md)
accounts for four `3EA` address opportunities and four `3EC` writes per
ADC visit; its earlier claimed sample-paced timing was invalid. With
`3F9` latch and `3FA` return, all four stimuli sustain the receive loop,
and frozen RAM affects `3FA` in the common tail. `3F8` and `3F9` stay
unchanged, while the late `3FA` own-echo proxy grows rather than shrinks.
With `3EB` return, complete PROM trace digests still match no-feedback
controls. These routes do not demonstrate echo cancellation. The
[high-nibble `3FA` return test](g2/JOINT-MASK04-RAM-HIGH-RETURN-EXIT.md)
now tests that alternative with the corrected sample-paced write gate:
under the assumed previous-overflow TEST source, write-only and
read-only controls complete 3,000 ADC visits, but
`3F9`-latched and `3FA`-latched high feedback leave the four-row loop
after 939 and 423 visits. Both exits occur before the sample-25 pulse;
the `3F9` pulse and baseline traces are identical. Following `3EE`,
both routes take a 53-word transition and then alternate at `1E9/1EA`
for the remainder of the 96,047-word run, with no further ADC reads.
The [TEST-source screen](g2/JOINT-MASK04-RAM-CONDITION-RESCUE.md)
checks all sixteen timing/flag/polarity choices on the legal waveform.
Previous sign, carry and overflow alone sustain the no-feedback loop;
with the same high return, sign exits at 236 visits, overflow at 939,
but **previous carry completes 3,000**. The
[own/remote/mixed challenge](g2/JOINT-MASK04-RAM-CARRY-ECHO-SCREEN.md)
then runs that surviving candidate for eight 288,047-word cases,
all sustaining 9,000 visits. Yet the late `3FA` mixed-versus-remote
code-space difference grows from 0.439 in write-only control to 17.796
with feedback, with 658→1,312 differing visits. Frozen RAM affects
the first three common-tail samples but this is not selective echo
attenuation. Keep TEST and RAM wiring assumed; try a signed or
mode-qualified return or another output site with the same controls.
The [training arithmetic audit](g2/JOINT-MASK04-RAM-CARRY-ARITHMETIC.md)
checks every one of 24,000 reached `3FA` words in those four feedback
runs. Pre-word R10 is always `10` at this site, although it changes
elsewhere; with RAM D low nibble forced to `1`, the executed output is
`Yhi=(Dhi+2)&15`, `Ylo=carry_in`. The stored high nibble and current
carry explain this candidate output without a varying R10 estimate.
Seek a mode or feedback timing that puts trained state into a consumed
operand, or inspect another executed output before inferring cancellation.
C4 stays open and G2 active.
The [paired propagation trace](g2/JOINT-MASK04-RAM-CARRY-PROPAGATION.md)
now compares that previous-carry, high-nibble return with the same-input
write-only control across 96,047- and 288,047-word runs. Only `3FA` ALU
and R13 writes differ (1,219 and 6,000 times); each R13 difference lasts
six cycles and is overwritten at `3FC`. PC, Q, TEST and all later ALU
words agree. Test an external `3FA` latch with a line consequence, or a
photo-compatible feedback route that reaches a later consumed operand;
do not treat transient `3FA` code contrast as a proven echo residual.
The missing latch/return wires are hypotheses, not goal blockers.
The [sample-paced `3FA` latch screen](g2/JOINT-MASK04-RAM-CARRY-LATCH-PHASE.md)
replays the four own/remote/zero controls on both write-only and high-return
routes. `3FA` Y is constant across all 47/46 visits within every held ADC
sample in all eight runs, so all 46 fixed latch phases capture the same
byte. Late mixed-versus-remote code difference is 0.4375 in the control
and 17.8125 with return at every phase; a phase choice cannot rescue
this particular residual proxy. Seek a consumed trained operand or an
explicit photo-compatible analog output circuit next; keep C4 open.
The [alternative `3FC` RAM return](g2/JOINT-MASK04-RAM-CARRY-3FC-PROPAGATION.md)
does reach another executed operation: on both legal streams it changes
`3FD` arithmetic and its Am27S31 read (1,219 and 6,000 visits), while
the four-row PC path, Q and TEST remain equal to write-only controls.
R10/R13 state then rejoins, with no later changed ALU site. Compare
`3FD` Y across own, remote, mixed and zero training/freeze controls
before treating it as an echo residual. Keep the `3FC` RAM mux and output
latch explicitly assumed; neither is a goal blocker.
The [four-input `3FD` challenge](g2/JOINT-MASK04-RAM-CARRY-3FD-ECHO-SCREEN.md)
now does that comparison for eight full-PROM runs. Write-only `3FD` Y
does not distinguish the inputs; high return makes it input-sensitive,
but late own-echo-versus-zero contrast grows from 29.824 to 35.840
and mixed-versus-remote from 40.853 to 44.907. Its Y is constant
within each held sample, so all 46 fixed latch phases retain that
increase. Only the first three tail samples differ from write-only after
freeze. This tested `3FD` code is a delayed-input transform, not a
selectively falling echo residual. Audit its arithmetic/ROM operands or
try a distinct photo-compatible return; keep C4 open and G2 active.
The [48,000-word `3FC→3FD` arithmetic audit](g2/JOINT-MASK04-RAM-CARRY-3FC-ARITHMETIC.md)
now explains that route: at all 24,000 training `3FC` visits,
R10=`10` and carry-in=0, so `Y3FC=(RAM_D+0x10)&0xff`; this selects
the following real-ROM address. At all 24,000 `3FD` visits, R5=`00`
and carry-in=1, so `Y3FD=(((ROM>>4)+1)&15)<<4`. Five reached RAM
codes map to four output codes, with `31`/`91` colliding at `20`.
The delayed input is recoded, but no varying trained coefficient enters
either checked operand under this fixture. Seek a distinct mode/return
or independently constrained line route; keep C4 open and G2 active.
The [held-mode RAM pulse test](g2/JOINT-MASK04-RAM-MODE-PULSE.md) now
combines that corrected sample-paced memory route with candidate `D3EB`
values `01`, `81`, `A1` and `C1`, plus synthetic `81→A1` and `81→C1`
edges at freeze. All six preserve the same one-byte RAM change and a 47-visit delayed
`3FA` pulse; their write-only controls
have no delayed pulse. `A1` shifts the `3FA` upper nibble but does not
gate the stored low-nibble response. Held `C1` and `81→C1` produce the
same `3F8`/`3F9`/`3FA` Y bytes and frozen RAM as `81` in every paired run,
despite different full traces. This narrows a simple held-mode
explanation under that one edge timing, not a paced controller gate or
physical RAM circuit. Next test a candidate write-enable or return
route under paced controller traffic against own/remote/mixed controls;
keep C4 and G2 active.
The [delayed-return arithmetic check](g2/JOINT-MASK04-RAM-RETURN-ARITHMETIC.md)
then verifies all 282 reached `3FA` words while the changed RAM address
is read under `01` at three- and sixteen-sample lags and `A1` at three.
The actual split instructions are `55/C5`: low D-minus-R10 arithmetic,
high D-plus-R10 arithmetic, with only R13's high nibble written. The
stored pulse changes Y's low nibble but leaves matched Q and written
R13 identical. This candidate output is a transient mixed-nibble
calculation, not a demonstrated full-byte echo residual or receive
decision; keep C3/C4 open and seek a functional consumer or alternate
return rather than inferring cancellation from RAM activity.
The [controller-frame D3EB test](g2/RECEIVER-MASK04-FRAME-MODE-3EB.md)
shows that a labelled `81→A1` mode-byte edge changes several executed
registers but leaves no post-edge history or conditional branch under
this direct input route. Revise the mode lane or output hypothesis and
keep C4 active.
The [frame-byte receive-decision replay](g2/RECEIVER-MASK04-FRAME-MODE-DECISIONS.md)
now tests that same direct `3EB` hypothesis against the frozen two-visit
readout. At 75° and 165°, held `01`, held `81`, held `A1` and a boundary
`81→A1` edge give different full-PROM traces but identical Y5–Y7
capture features and 15/15 known dibits in each case. This does not
establish the physical frame route or echo freeze; it shows that those
controller bytes need not disrupt the candidate C3 readout under the
tested stimulus. Challenge longer streams and the USART handoff while
seeking a separate mode-qualified residual path for C4.
The [long frame-mode handoff](g2/RECEIVER-MASK04-FRAME-MODE-ZERO-HANDOFF.md)
now does that challenge: two 768,047-word PROM runs offer the hypothetical
`81→A1` frame byte at `3EB` across 32 preamble and 32 data symbols.
Both recover all 63 measurable dibits, the controller's eight actual
scrambled zero-run line bytes, and `AF→B0` only with an aligned external
SYNDET pulse. Their full traces differ from the `01`-mode baseline.
The frame-byte and serial wires, symbol clock and sync source remain
hypotheses; C3 and C4 stay open. Test those photo-compatible routes or
another natural timing fixture rather than waiting for continuity.
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
The [mask-04 `3FA` capture replay](g2/JOINT-MASK04-3FA-GATE-COLLISION.md)
finds that either three-literal raw-PROM decode can clock a candidate latch
at all 3,000 `3FA→3ED` receive transitions. It preserves the `1F`/`6F`
one-sample distinction lost by the proposed U12 row pair (`20` versus
`21` on 47 held visits), while a legal rotated eight-symbol stream yields
only those two latch bytes. Test a temporal or multi-signal consumer and
serial route next; the untraced nets are assumptions to test, not blockers.
The [two-visit `3FA` Y0 screen](g2/RECEIVER-MASK04-3FA-TWO-VISIT-BITS.md)
now runs six legal rotated-carrier PROM streams and tests all 70,125
fixed visit pairs against independent dibits. None yields a fully known,
unambiguous training lookup; the best knows 11/24 training dibits, and
the frozen choice makes 1/24 and 3/24 wrong decisions on two new seeds.
This rejects only the specified one-bit/two-visit candidate. Continue
with a photo-compatible multi-signal consumer or longer phase-aware
history; C3 and G2 remain open.

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
