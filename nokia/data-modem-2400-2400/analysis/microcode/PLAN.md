# DSC2847 microcode emulation plan

> **Status:** complete ([final review](assumed/FINAL-REVIEW.md)). The current
> goal is **G2** in [PLAN-2.md](PLAN-2.md#goal-g2). G2 remains active when a
> photographed connection is ambiguous: model the plausible connections as
> labelled assumptions, run them, and use the results to choose the next test.

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
The [D349 source-update experiment](g2/PHOTO-TABLE-SOURCE-UPDATE.md) is a
concrete example: after two restart fixtures gave fixed table sources, four
other photo-compatible scenarios found an input-sensitive R5 write before
later table calls. That conditional path is a lead to test with changing
inputs, not a claim about the board's untraced wiring.

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
its source, but the lower- and upper-bank runs at 12C behave differently
([comparison](g2/SWAPPED-ROM-LOOPS.md)). Test fixed and, where the modeled
interface permits it, changing bank choices as labelled scenarios. Use the
resulting control flow and ROM addresses to narrow the candidates; do not
promote a useful bank choice to a traced connection.

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

An unknown physical net is never, by itself, a G2 blocker. If the available
photo-compatible candidates all fail, record what each run excluded and pivot
to a new mapping, timing model, stimulus or independent program/signal clue.
Only consider a goal-level blocker after showing that no such experiment can
advance the acceptance checks; a failed candidate or a missing continuity
measurement does not meet that test.

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
