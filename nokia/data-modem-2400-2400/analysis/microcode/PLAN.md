# DSC2847 microcode emulation plan

> **Status:** complete ([final review](assumed/FINAL-REVIEW.md)). The current
> goal is **G2** in [PLAN-2.md](PLAN-2.md#goal-g2). G2 remains active when a
> photographed connection is ambiguous: model the plausible connections as
> labelled assumptions, run them, and use the results to choose the next test.
> Missing continuity data is not a reason to mark G2 blocked.

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
**Status rule:** report G2 as active with the current uncertainty and the next
bounded experiment whenever a photo-supported connection, timing or input
hypothesis can still be tested. A failed run closes that hypothesis under its
recorded fixture; it does not block G2. Reserve "blocked" for the case where
the available evidence supports no runnable candidate and no independent
controller, PROM or signal analysis can advance an acceptance check. Do not
ask for more photos or continuity measurements as a prerequisite while those
routes remain open.
**Default decision:** keep the goal active and run a photo-compatible baseline
plus a few meaningful alternatives whenever a connection is uncertain. Mark
only the tested candidate as unsuccessful when it fails; do not mark the goal
blocked or request new measurements while another runnable hypothesis or
independent program/signal analysis remains. State the next experiment in the
result summary so an ambiguous photograph leads to another action.
An acceptance check that has not passed is **open**, not automatically blocked.
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
Only consider a goal-level blocker after showing that no such experiment can
advance the acceptance checks. Before calling something blocked, write down
the concrete next experiment attempted, its result and why no alternative
candidate, stimulus or independent analysis remains. A failed candidate or a
missing continuity measurement does not meet that test.

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
the third-row ROM address on 1,359 visits, but the fourth row makes complete
RAM/Q state identical to the control on all 1,500 visits. Keep this path as
a conditional transient-input candidate, not a recovered receiver. Test a
third-row latch or a different dispatch/condition route next; do not treat
the absent pin trace as a blocker.

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
