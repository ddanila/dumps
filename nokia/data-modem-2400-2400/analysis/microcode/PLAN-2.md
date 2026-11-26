# Plan 2: establish what the Am2901 microprogram does, and why

## Goal G2

> **Show what the DSC 2847 microprogram does in the modem, and how, by
> running it.**

In full: identify the signal-processing job of the Am2901 board (expected:
V.26 ter DPSK modulation, demodulation and echo cancellation). Narrow the
candidate field mappings to one that implements it. Then demonstrate it in
the emulator: driven by the real 8031 controller's commands and bitstream, the
microcode should produce the expected line signal.

- **"What" is reached** when the identification holds at ≥80% confidence.
- **"How" is reached** when the emulated transmitter passes, plus the
  receiver or the echo canceller.

The exact criteria are in [§3](#3-acceptance-for-g2).
Unknown board connections are **active hypotheses, not a G2 blocker**: use
photo-compatible candidates with recorded pin-direction and timing assumptions,
run bounded tests, and revise candidates when the evidence changes. Physical
continuity checks in Phase B can resolve them, but are not required before
continuing Phases A and C. Follow the [working rules](PLAN.md#uncertainty-is-a-reason-to-experiment-not-a-goal-blocker)
without relaxing the acceptance criteria.

## Why a second plan

Goal G1 in [PLAN.md](PLAN.md), running the microcode without errors under
explicit assumptions, is complete: the microcode now runs under six candidate
field mappings and every word has an annotation. That bottom-up approach
reached its limit. Its own [final review](assumed/FINAL-REVIEW.md) states that
it does not identify the algorithm, and the integrated DAC experiment only
produces constant codes. Plan 2 works top-down. It first establishes which
standard the modem implements. That standard then predicts what the DSP must
compute, and those predictions decide between the field mappings.

## 1. New evidence (2026-11-24)

These findings come from public specifications, the existing 8031 analysis
and the photographs. None of them depends on an unverified microcode mapping.

| # | Finding | Source | Confidence |
| --- | --- | --- | --- |
| E1 | The 8031 scrambler pair (d = 18 or 5, length 23, selectable per direction) is exactly V.26 ter §5: GPC = 1+x⁻¹⁸+x⁻²³ (call), GPA = 1+x⁻⁵+x⁻²³ (answer). V.26 defines no scrambler, V.26 bis has none and V.22/V.22 bis use 1+x⁻¹⁴+x⁻¹⁷. V.32 uses the same pair, but it runs at 4800–9600 bit/s. | [controller SCRAMBLER](../controller/SCRAMBLER.md), ITU-T V.26 ter (11/88) §5, §6.1 | High |
| E2 | Under Intel 8251A semantics, the USART at 01/05 is programmed `CC` + sync char `FF` + `15`. That is synchronous mode with 8-bit characters, external sync detect, and Tx/Rx/error reset enabled. Scrambled bytes are written to 01 and descrambler input is read from 01. **USART 01/05 is therefore the synchronous line-side bitstream to and from the modem DSP.** USART 02/06 takes `6E`/`7E`/`6A`/`66` (async ×16, chosen by switches) or `EC` (sync), so it is the DTE port. V.26 ter specifies exactly these DTE modes: synchronous or start-stop. | [controller PROGRAM](../controller/PROGRAM.md), 8251A data sheet | High (semantics); the physical net still needs tracing |
| E3 | Timer 1 reloads FC21. With the 11.9808 MHz oscillator on DSU 3556, that gives **0.9926 ms from reload to overflow** on a classic 12-clock 8051; interrupt/reload overhead makes the software tick approximately 1 ms, but its exact period is unmeasured. The state machine at 1000–15xx (state in RAM34, countdown in bank-2 R7:R6) loads 1805, 2605, 250, 2000, 455, 60, 70 … countdown ticks. Their approximate durations match the V.25/V.26 ter operating-sequence windows: ≥1.8 s silence (2.15 ± 0.35), ≥2.6 s 2100 Hz tone (3.3 ± 0.7), 250 ms silences, the 2 s rate-pattern timeout and a 500 ± 50 ms echo-suppressor-disable tone. | `controller-linear.asm` 11B6–11E3 etc., V.26 ter §6.3 | Medium-high (state-by-state mapping not yet done) |
| E4 | The boards are date-coded 8406/8410 and their ICs 1983. V.26 ter was approved in 1984. The front panel reads "2400/2400" (duplex), unlike Nokia's DS2839 "2400/1200" (V.26 bis-like). | Photographs, collector listings | Medium |
| E5 | The DSC2847 has its own **14.400 MHz** oscillator (CK1144AC). 14.4 MHz = 1500 × 9600 = 12000 × 1200 baud = 8000 × 1800 Hz. | Whole-board photo, `board/inventory.json` | Fact; the microcycle divisor is unknown |
| E6 | Am27S31 bytes 00–13 are a 16-point sine plus 4 wrap entries, which allows sin(i) and cos(i) = table[i+4] without wrapping, i.e. quadrature. 1800/9600 = **3/16**: at a hypothetical 9600 Hz sample rate (8 samples/baud), the 1800 Hz carrier advances exactly 3 entries per sample. 100–140 is a 65-entry quarter sine, i.e. a fine 256-step phase, as needed for carrier tracking (V.26 ter requires ±7 Hz). 68–6F `00 01 02 03 01 00 02 03` looks like a dibit/quadrant map. 141–1CF are smooth signed curves that resemble filter or AGC coefficient tables. | ROM bytes | Shapes are facts; their roles are hypotheses |
| E7 | DED 3558 visibly carries a stickered **ADC0800PCD**. National Semiconductor specifies an 8-bit A/D converter with internal successive approximation and complementary, latched digital outputs. This is a concrete candidate for receive samples; its bus route and sample timing are untraced. The earlier claim that this photographed device was a DAC0830 was incorrect. | [photo and component evidence](g2/ADC0800-INPUT.md) | High for part marking and component function; physical route unknown |
| E8 | A separate 16-pin device in DED 3558's lower analog section is marked `DAC 08` / `HP`, consistent with **DAC08HP**, an 8-bit current-output D/A converter. Adjacent 74LS273 and 74LS373 devices are candidate sample-code and hold latches. This supplies a concrete output-converter candidate, but the bus direction, input nets, latch controls and analog output route are untraced. The earlier DAC0830 two-register sink is a counterfactual, not the observed part. | [photo and component datasheet review](g2/DAC08-OUTPUT.md) | High for visible markings and component functions; medium for latch roles; routing unknown |
| E9 | Executing controller routine 1C07 over all octets shows that state 83 marks exactly the rotations of V.26 ter's first five rate-pattern representatives (`01 03 05 07 09`), and state A6 marks exactly the first two. In a preserved-RAM probe, four identical marked octets advance state 83 to 84; three or an interrupted sequence do not. This independently matches the standard's four-consecutive-octet detection rule, but the probe directs the PC between routines and does not establish the physical receive path. | [executed comparison](g2/PATTERN-CLASSIFIER.md#comparison-with-v26-ter-rate-patterns), ITU-T V.26 ter §6.1.3 and §6.3.1.2 | High for executed set and state transition; protocol role strongly supported but still conditional |

For E2, `CC` sets the 8251A's **external** sync-detect bit. The programmed
`FF` character is a transmit fill candidate; it does not make the
line-side receiver hunt internally for `FF`. C3 therefore needs a
photo-compatible source and timing hypothesis for SYNDET pin 16 as well
as RxD and RxC. See the [external-sync handoff](g2/RECEIVER-MASK04-EXTERNAL-SYNC-HANDOFF.md).

**Working conclusion:** the modem is very probably a V.26 ter-class 2400 bit/s
duplex echo-cancelling modem (1800 Hz carrier, 1200 baud, 4-phase DPSK, 100%
raised cosine split between Tx and Rx). The 8031 handles the DTE, scrambling,
the V.25/V.26 ter handshake and the front panel. That leaves the Am2901 board
with the sample-rate work: **DPSK modulation with pulse shaping, demodulation
(AGC, carrier/timing recovery, differential decision), and adaptive echo
cancellation**. The four MCM93422 RAMs on DSC 3557 (256×4 each) fit an
echo-canceller delay line and tap store. The initial estimate was about 75%;
E9 strengthens the controller's V.26 ter identification, but it does not yet
demonstrate that the Am2901 executes the inferred signal-processing job.
Phase A below is designed to push it past 80% from desk work alone, and
phases B–C turn "what" into "how".

## 2. Phases

### Phase A: desk work that does not need unknown wiring

- **A1 Pin the standard from the 8031 side.**
  - Map each RAM34 state (A0, A1, A2, A3, B8, 80, 83, 98 …) and its timer to a
    V.25/V.26 ter step: silence, 2100 Hz tone, sequence B rate patterns,
    sequence C echo training, data.
  - Find the rate-pattern octet handling (32 repetitions, "4 error-free
    octets", the 34 legal octets) and the "64 consecutive scrambled zeros"
    detector.
  - Run the existing 8031 harness through a scripted call: synthetic line
    events, USART-01 receive bytes and status.
  - *Done when* every V.26 ter operating-sequence step has an identified state,
    or a contradiction rules out V.26 ter (then retest against pre-standard
    variants and V.26 4-wire).
  The [A4 pattern comparison](g2/CONTROLLER-SEGMENT2-PATTERN.md) now gives a
  strong state-specific witness: on the `40`/`60` branches, two A4 blocks in
  each unchanged-8031 run contain the exact 64-bit V.26 ter segment-2 GPC/GPA
  pattern, starting at bit 1 of the first A4 port-01 byte and taking the last
  bit from the first A5 byte. Table 3's printed 38-bit prefix and Appendix
  I's scrambler recurrence independently predict all 64 bits. No other exact
  window occurs in the four 64-iteration streams. A4 is therefore a strong
  digital segment-2 candidate; the one-bit boundary, natural timing and line
  output remain unresolved, so A1's full state map is not complete.
  An [interrupt-paced 8031 continuation](g2/MAIN-LOOP-TIMER1-SEGMENT2.md)
  replaces per-poll countdown expiry with Timer 1 interrupts while explicitly
  holding the separate RAM15 sign gate positive and TxRDY high. Both `40` and `60` paths
  then spend 34 polling passes in A3 with **no port-01 writes**, followed by
  exactly eight A4 `FF`-source bytes and the first A5 `03`-source byte.
  Those nine bytes exactly match the forced-timer source used in the DSC
  PROM calibration and again contain the full 64-bit GPC/GPA pattern.
  The first A3→A4 boundary spans 25 modeled timer interrupts. A3 is a
  stronger segment-1 candidate, but the CPU timer model, RAM15 gate,
  physical symbol timing and 180° line reversals are not established.
  A [state-AF zero-run execution](g2/ZERO-RUN-DETECTOR.md) adds a separate
  sequence-C witness. With both V.26 ter scrambler polynomials and nonzero
  history, eight received zero-source octets pass through the actual 8031
  USART-read, descrambler and zero-counter ROM dispatch and advance `AF→B0`;
  seven remain at `AF`, while a nonzero byte resets the count. This matches
  the standard's 64-consecutive-zero step at octet alignment. From the same
  controller image, the subsequent four-byte send changes from
  `D0 42 89 9A` at `AF` to `D0 42 81 1A` at `B0`, clearing two frame bits.
  The final state-step handoff is synthetic, and the DSC receive/echo route
  is still unverified, so A1's complete operating-sequence map and C3/C4
  stay open.
  A [photo-compatible AF/B0 frame-route screen](g2/PHOTO-AF-B0-FRAME-ROUTES.md)
  now feeds those executed frames into two candidate DSC inputs. The reached
  `D38E→39E` byte relay ignores both changed bits, so its ALU output and
  selected ROM address stay fixed. Four of eight held-`D127` CD4094 lane/order
  candidates change the running PROM trace. This narrows candidate command
  routes but does not demonstrate a continuous DSP transition or echo
  cancellation; use the changed bits as a differential stimulus for C4.
  A [literal A3-frame route screen](g2/PHOTO-A3-HELD-FRAME-SEGMENT1.md) then
  tests all six distinct frame-byte values as held candidate D127 inputs
  with no port-01 data. Three even bytes sustain 32-symbol, 384,256-word
  PROM runs but their carrier-relative phase drifts; none retains an
  alternating 180° offset. The three odd bytes leave the first loop after
  61–221 ROM reads in the prior all-byte screen. A direct held byte in this
  q3 loop therefore does not generate A3's required segment-1 pattern.
  Test a decoded command, symbol-rate idle source or different microcode
  loop without treating the untraced connection as a blocker.
  A [continuous A3→A4 PROM replay](g2/PHOTO-SEGMENT1-TO-SEGMENT2-CONTINUOUS.md)
  now gives that idle-source hypothesis a bounded test: 32 assumed `11`
  dibits followed by the controller's exact A4/A5 GPC or GPA dibits run in
  one 768,256-word q3 trace per selector. All 12 candidate DAC bus orders
  decode 62/62 aligned decisions, with the required A3 half-turns and no
  phase reset at A4. An unmodulated `00` control misses 31 decisions.
  This demonstrates conditional continuity, not the physical A3 source or
  line output. The [8251A sync-fill audit](g2/USART-SYNC-FILL-SEGMENT1.md)
  supplies a concrete source for the assumed `11` dibits: the controller
  programs `FF` as the synchronous USART's single fill character, and the
  8251A sends it automatically when no data character is available. The
  executed A3 interval has no data writes or USART reprogramming. Its first
  A4 byte contributes one extra bit (`1` for GPC, `0` for GPA) before the
  exact segment-2 window; the prior DSC replay omitted that bridge bit.
  A raw-bit pairing screen gives 0/62 aligned errors for GPC at bit offset 1,
  but **1/62 for GPA** at that offset; offset 0 gives 15 and 16 errors.
  The GPA offset-1 input was checked in a fresh 768,256-word PROM run.
  Next test the bridge's symbol timing or a photo-compatible decoder rather
  than silently dropping it. CTS, Tx clock and the physical DSC route remain
  assumptions; G2 stays active.
  A [TxRDY-paced controller/8251A replay](g2/MAIN-LOOP-USART-TXREADY.md)
  then models the one-byte transmit buffer and a 2400-bit/s shifter at eight
  byte-clock phases per selector. Each run shifts the same nine bytes onto
  candidate TxD, including the exact 64-bit segment-2 pattern. Waiting for
  buffer space moves the eighth `FF`-source CPU write from A4 into A5, but
  does not delete it. `FF` sync fill continues until the first data byte
  starts; sampled phases provide 59–68 fill bits after A3 entry, so a
  32-symbol segment-1 window is timing-compatible. The exact clock phase,
  bridge-bit pairing, physical DSC route and line waveform remain open.
  The [USART boundary-event screen](g2/USART-TXRDY-BOUNDARY-GATE.md) finds
  that a fixed delay after TxEMPTY falls cannot align the first data bit
  across the sampled phases: it takes 1–8 bit-clock edges. In the one-byte
  model, TxRDY rises when that first bit shifts out. A labelled decoder
  triggered by that rise and skipping the bridge bit reproduces the exact
  inputs of the earlier zero-error DSC PROM runs for both selectors.
  This narrows the candidate gating logic; the TxRDY wire and bit-skip
  circuit remain untraced and C2 remains open.
  A [nine-offset data-start screen](g2/USART-DATA-START-ALIGNMENT.md)
  then uses the actual TxRDY-paced nine-byte stream and a 64-bit `FF`-fill
  window. Only starting at the second shifted data bit gives 0/62 aligned
  errors in both modes across all 12 candidate DAC buses; the other eight
  starts give at least 14 errors. Two neighboring starts were run through
  the real PROM as controls. This constrains a possible input gate, but the
  output DAC clock/bus and line waveform still need independent evidence.
- **A2 Define the controller-to-DSP command interface.**
  - Decide what tells the DSP "send 2100 Hz", "send reversals", "send data at
    1200/2400", "train/freeze echo canceller" and "call/answer". The leading
    candidate is the 4-byte mode-0 frame (the fourth byte is a 5-bit state
    code + 3 flags, and RAM34 is the state). Other candidates are P1 bits, the
    MOVX 8004 read, and the 8251 #1 modem-control pins (RTS/DTR/DSR/SYNDET).
  - Produce a table `state → frame bytes → expected DSP behaviour`.
  - This replaces the arbitrary "c,p,l,h" bridge in
    [FRAME-DAC-BRIDGE](assumed/FRAME-DAC-BRIDGE.md) with meaningful inputs.

  A [preserved-image receive/state/send run](g2/RECEIVED-CHAIN.md) now proves
  that a USART-received byte selects four distinct controller state/frame
  chains under forced expiry events. Replaying their actual outgoing bytes
  through an [assumed DSC D38E route](g2/RECEIVED-CHAIN-MICROCODE.md) changes
  reached `39E` ALU values, but only by the previously identified byte-field
  relay. The frame destination and tone/training/data meanings remain open;
  this conditional bridge does not complete A2 or G2's transmitter test.
  The [DSU 3556 photo review](g2/DSU3556-SHIFT-REGISTERS.md) identifies four
  CD4094BE shift-and-store registers, enough parallel stages for the four
  transmitted bytes. Their cascade and destination are untraced, but this
  makes a held control word a more direct candidate than presenting outgoing
  bytes to D38E one at a time. Under that [held-byte hypothesis](g2/PHOTO-LATCHED-FRAME.md),
  all 16 controller-class/byte-lane runs settle to constant `39E` values.
  Continue by testing which latched bits could alter control flow or a
  sustained sample path; the physical output route remains open.
- **A3 Characterise the Am27S31 regions as DSP tables.**
  - Fit 141–1CF against raised-cosine and root-raised-cosine pulses at 8 (and
    4, 6, 12) samples/baud, Hilbert/interpolator taps, 1/x, log/exp and AGC
    curves.
  - Test 68–6F against the V.26 ter Table 1 Gray mapping (00→0°, 01→90°,
    11→180°, 10→270°).
  - Characterise 30–7F as potentially mixed parameters and signed sequences.
    Test phase-step interpretations such as 48/56 at 9600 Hz against actual
    read addresses and dataflow before assigning any byte that role.
  - Record negative results as well.

  The [shape-control comparison](g2/README.md#first-independent-rom-constraint)
  finds a high wide-rate RRC fit at 40 samples/symbol, but a free sine fits
  the same `16F–1CF` bytes equally well and neither reproduces a quarter of
  the rounded values exactly. Do not identify this region as a pulse filter
  from shape alone; find its actual address sequence and arithmetic consumer.
  The [q1/q2 D127 input screen](g2/PHOTO-127-12C-EXCLUSIVITY.md) tests one
  such consumer route. With the fitted ROM gate changed to leave D127 as an
  external input, only D127=`00` in q1 and five bytes in q2 enter PC12C ROM
  feedback; the rest revisit D127. The real-controller scrambler bitstream
  consumes one bit in forward order, or six in reverse, before the fixed
  table loop. Neither case reaches candidate output `392`. This fixture
  does not show controller-driven pulse shaping; pursue a different gate,
  input route or retained-state path.

  The [D127 two-bank execution](g2/PHOTO-127-BANK-COMPARE.md) tests the
  tempting 16-point-sine path directly: lower-bank reads leave addresses
  `000–00F` after four D127=3 steps, and the upper-bank read traverses its
  quarter-sine region plus unrelated regions. Signed upper-bank ROM bytes
  peak at the chosen 1800/2100 Hz step frequencies, but the same peak follows
  seven other tested step values. This is a ROM harmonic under assumed timing,
  not yet a carrier sample stream or recovered address-folding circuit.
  A [paired A8 liveness check](g2/PHOTO-127-LIVENESS.md) now isolates the
  `129` operand: changing its bank changes 249/253, 694/740 and 717/740
  selected bytes for D127=1, 48 and 56, respectively. The following `12A`
  ALU value changes less often, and every paired post-`128` RAM/Q/flag/stack
  checkpoint is identical. Under this fixture the ROM effect is transient;
  test a photo-compatible latch phase at `129`/`12A` or another retained ROM
  route, without treating the missing trace as a blocker.
  A [raw-bit clock screen](g2/PHOTO-127-CLOCK-SCREEN.md) finds 11 PROM-bit
  edge choices at every `129` visit and six at every `12A` visit for both
  D127=48 and 56. A direct, unqualified edge would recur every four
  microinstructions: 0.9–3.6 MHz for the hypothetical `14.4 MHz / k`,
  `k=1…4` clock, rather than 9,600 Hz. The divider and latch clock are
  untraced; test a qualified clock or another repeated output site.
  A [photo-B5 tone-step screen](g2/PHOTO-DAC-B5-TONE-STEP.md) now clocks a
  candidate LS273 at each PC129 and enumerates all eight Y-bit sources for
  its D4 input, using the photographed DAC08 B5←Q4 segment. With upper-bank
  ROM reads and hypothetical 9600 samples/s, only Y7→D4 peaks at both
  1800 Hz for D127=48 and 2100 Hz for D127=56. Lower-bank D127=48 instead
  peaks at 3600 Hz on that bit. All nine tested upper-bank increments peak
  at their own step frequency, so this is a constrained phase-dependent
  output-bit candidate, not proof of Nokia's tone values, sample clock,
  full DAC code or carrier output.
  A [fast-clock alias screen](g2/PHOTO-127-CLOCK-ALIAS.md) checks the PC129
  phase/ROM/Y recurrence against 740 executed reads, then projects all
  distinct 9,600 Hz gate alignments for 14.4 MHz microinstruction divisors
  1–4. Every step-48 B5 peak moves to 1,500–4,200 Hz and every step-56 peak
  to 150–4,725 Hz; none remains at 1,800/2,100 Hz. A one-visit-per-sample
  clock would need 375 oscillator periods per four-word-loop instruction.
  The divider is untraced, so revise timing, effective step or output path
  rather than treating this as a physical transmitter rejection.
  A [fast-step candidate screen](g2/PHOTO-127-FAST-STEP-CANDIDATES.md) now
  executes eight alternative D127 bytes and solves the exact sampled phase
  equation for the integer fast-clock cases. Divisor 1 admits forward
  1800/2100 steps `50/88`; divisor 3 admits `F0/98`, with reverse alternatives
  `B0/78` and `10/68`. Their projected B5 series peaks at the target under
  every start phase. The fractional divisors 2/4 cannot give a uniform phase
  step with one fixed nonzero D127 byte. Two candidate values (`F0`, `10`)
  occur in the ROM `30–7F` region, but their connection to D127 is unknown.
  A [signed-ROM structure check](g2/ROM-ANTISYMMETRIC-REGIONS.md) now shows
  those two bytes are opposite positions of one exact anti-symmetric
  16-byte window. This weakens the parameter-source interpretation: a q3
  lower-bank scan reaches them only as part of an almost full-ROM sweep,
  without retained PC128 state. Keep the fast-step equation as a timing
  possibility, and seek an actual controller-selected source for D127.
  A [controller-frame lane screen](g2/PHOTO-127-CONTROLLER-FRAME-STEPS.md)
  then feeds the observed A0/A1/A2 frame bytes directly into D127 under the
  same assumptions. Only A0/A2's literal third byte `88` matches a fast-clock
  2,100 Hz step; A1 has no exact step match, and its distinct `81` byte exits
  the PC129 loop after 125 reads. A literal held frame lane therefore does
  not explain a sustained A1 tone in this fixture. Test an intermediate ROM
  parameter selection, another controller route or another sample site.
  A [full D127 parity screen](g2/PHOTO-127-PARITY-EXIT.md) runs all 256 held
  bytes and shows why the `81` case exits: every odd byte reaches phase zero,
  branches at PC12A, scans 255 upper-bank ROM bytes at PC12E and waits at 084;
  every even byte stays in the PC127 loop for the tested 3,000 instructions.
  The PC12C input is a constant scenario stub, so vary that source and the
  controller-frame selector before assigning these paths modem roles.
  A [PC12C all-byte run](g2/PHOTO-12C-PHASE-SCAN.md) now shows a second exact
  input-stepped ROM-address recurrence after the `81` exit. All odd held
  PC12C bytes finish at phase zero and wait at 084; all even bytes keep the
  second loop active for the 3,000-instruction fixture. No candidate output
  word is reached. Feed a changing controller-derived PC12C source and trace
  whether the selected ROM byte survives to state or an output latch.
  A [paired PC12E bank test](g2/PHOTO-12C-BANK-LIVENESS.md) shows 251
  different selected ROM/Y values and 69 carry-dependent R0 values, but
  no state difference after the next PC12D. A changing PC12C input alone
  therefore does not establish retained ROM feedback in this fixture;
  test a photo-compatible latch at the transient site or another mapping.
  A [controller-bitstream PC12C run](g2/PHOTO-12C-CONTROLLER-STREAM.md)
  now feeds 128 ROM-executed 8031 scrambled bits under four hold schedules.
  The input changes the selected ROM address, but 1/2/4-visit holds finish
  the bitstream without leaving the loop, and eight-visit holds exit before
  all bits are presented. Paired bank runs show no post-PC12D retained
  difference; none reaches `392`/`39E`. Revisit the input route, mapping
  or a photo-compatible latch clock rather than treating this fixture as
  a transmitter demonstration.
  A [PC12E/PC12F latch-site screen](g2/PHOTO-12C-LATCH-TONE.md) executes
  all eight fast-step candidates in the second loop. Under a hypothetical
  Y7→LS273-D4, 9,600 Hz gated clock, both sites' B5 bits peak at the chosen
  1,800/2,100 Hz rate. PC12F's raw Y byte fits those bins almost exactly as
  well as the plain phase ramp, so the bit peak does not establish a DAC
  carrier. Resolve a plausible full-byte route and controller-selected step
  before treating either transient site as the transmitter output.
- **A4 Turn the reference algorithm into microcode signatures and re-score
  mappings.** For each candidate mapping, and for new ones the search may
  revive, test whether the microprogram contains:
  - a phase accumulator advanced by a constant (3/16 or 48/256) with wrap;
  - paired table reads at i and i+4 (or i and i+64);
  - a 4-way phase add of 0/64/128/192 driven by two input bits;
  - an 8-sample symbol loop;
  - 8-step shift-and-add multiply routines (the 1E9-style `PLP, BLT, POP`
    loops are candidates);
  - multiply-accumulate loops that address external RAM (93422) with an
    incrementing index;
  - a slow LMS-style coefficient update;
  - a receiver path that consumes ADC0800 complementary sample bytes, checks
    conversion-ready status or a buffered sample latch, and updates receive
    filter, timing, carrier or decision state. Test byte polarity alternatives
    until the physical bus route is known.

  A conditional A4 result is now available: under the held E4/I7/A0 photo-pin
  candidate, both 3C5 and 3DA tables [select the signs of duplicated source
  high bytes](g2/PHOTO-TABLE-EXACT.md). The rule matches all 140 reset-reached
  calls in that fixture. A [controller-dibit candidate run](g2/PHOTO-TABLE-DIBITS.md)
  then routes real 8031 line-side dibits through predecessor Y: q1/q3 select
  all four entries, while q2/q4/fitted-swapped stay at entry 3. The next
  discriminating check is whether the physical branch bus and input timing
  support that route and whether the values reach an advancing sample path.
  A [diagnostic AC=RST continuation](g2/PHOTO-TABLE-RESTART.md) repeats the
  controller-fed calls but leaves their source pair fixed, so the arithmetic
  path still needs a real ROM/data-driven source update before a transmitter
  interpretation is warranted.
  A [follow-up D349 candidate](g2/PHOTO-TABLE-SOURCE-UPDATE.md) demonstrates
  a conditional input-to-R5-to-table-output update in q3 under four other
  saved branch scenarios. This is a new input-route lead, not yet an advancing
  controller/ROM-driven source or a DAC sample stream. Test changing input
  candidates and output timing without waiting for a complete pin trace.
  A [controller-byte replay](g2/PHOTO-TABLE-CONTROLLER-SOURCE.md) confirms
  that actual USART-01 bytes can affect the q3 source under this candidate
  route, while the reached output word `39E` remains zero. The remaining
  transmitter task is a sustained input schedule and a changing DAC-bound
  output after the table calls. A dynamic register-flow check finds no read
  of the 1,056 table-written R10–R13 values in these 32 runs; test a branch
  or timing candidate that reaches a real table-output consumer.
  A [counterfactual E2 phase run](g2/PHOTO-TABLE-PHASE-CONSUMER.md) does reach
  such consumers: held low during table words and high elsewhere, the q3
  program passes actual controller bytes through D349, the sign table and
  instruction `140` (16 clean runs, 144 external table-output reads). The
  schedule is address-assigned, not a traced U5 clock; output candidate `39E`
  remains zero. Replace it with a plausible latch timing rule and continue
  toward a changing DAC-bound sample stream.
  A [real-PROM bit candidate](g2/PHOTO-TABLE-PROMBIT-CONSUMER.md) uses inverted
  U10 data bit 5 while keeping U10 enabled: it is low at all table words and
  high at four reached consumers. With real controller bytes and candidate
  dibit scheduling, q3 selects all four entries and carries a changing
  table result to instruction `140`. The inverter, U5 clock and both input
  routes remain untraced; `39E` still outputs zero. Test a physically timed
  latch and a continuing DAC path next.
  A [256-seed ordering screen](g2/PHOTO-TABLE-OUTPUT-ORDER.md) finds eight
  diagnostic paths with D349 → table → `392`/`39E` in time; four include a
  nonzero table-derived internal byte, yet none has a nonzero value at those
  candidate output words. Test a photo-compatible latch clock at `140`/`146`
  or another path from those consumers to DAC08.
  A [diagnostic LS273 replay](g2/PHOTO-TABLE-OUTPUT-ORDER.md#diagnostic-latch-at-the-internal-consumers)
  clocks `140` or `146` and captures controller-dependent bytes, but only
  one to three per run. The clock net and full data bus are untraced, and
  this does not satisfy the sustained transmitter check.
  A [U10 source/polarity screen](g2/PHOTO-U10-Q0-SOURCE-SCREEN.md) compares
  all eight real PROM data bits, direct and inverted. Only inverted bit 5
  preserves all 33 tested sign-table calls and nonzero downstream reads;
  the inverter and U5 connection are untraced. Use this as a targeted
  hypothesis, not proof of the physical mapping.
  A [stateful U5 clock replay](g2/PHOTO-TABLE-CLOCKED-U5.md) tests seven
  raw-PROM edges that match the required table/consumer levels in offline
  traces. All 168 controller-fed diagnostic runs retain 728 exact sign-table
  calls and 896 downstream reads, but no full trace matches the per-word
  reference. Only U11 bit 3 produces nonzero candidate output, a late fixed
  `FF` independent of the controller byte group. These specific direct-edge
  clocks do not establish a transmitter; test a decoded or external clock
  phase and the DAC latch route under labelled photo assumptions.
  A [raw-PROM clock-edge screen](g2/PHOTO-OUTPUT-CLOCK-BIT-SCREEN.md) finds
  six rising bits at every `140`/`146` consumer visit, but each also rises
  164–411 times in 2,500 microcycles. None is a direct 9,600 Hz sample clock
  under the plan's `14.4 MHz / k`, `k=1…4`, timing hypothesis. Test a decoded
  or divided clock, or a different repeated output path; the actual latch
  clock and microcycle divisor are untraced.
  A [separate-slice instruction screen](g2/INDEPENDENT-SLICE-FIELDS.md) now
  lets U8 decode an independent nine-bit PROM field under the candidate
  U8↔U2 control links. Two hypothesized U10/U11-lower and U17/U18-upper
  layouts visit D38E 128 times and select a ROM operand 127 times after
  the first D38E visit, versus zero in the shared-field fixture. Only the
  non-reversed layout actually selects the offered controller bits at D38E;
  the reversed-upper layout selects none. Both still read one fixed ROM
  address and hold `0B` at reached `39E`/`39F` sites;
  use the architecture change to search for a history-dependent path, not
  as a transmitter claim.
  A [D38C receive-input perturbation](g2/INDEPENDENT-SLICE-D38C.md) locates
  those repeated reads in the lower slice and substitutes reference ADC-like
  bytes at that site. The bytes change R6 at `38C`, but `3A0` overwrites it:
  all 128 complete loop-boundary states match the constant-byte control in
  both separated layouts. Look for a different retained input path rather
  than treating the restored ROM-read count as receiver evidence.
  The [recurring D-site screen](g2/INDEPENDENT-SLICE-INPUT-SITES.md) checks
  every selected D site in those two loops. Only D38E in the non-reversed
  layout and D3A1 in the reversed layout change a boundary state; a one-byte
  impulse survives for just one boundary at either site. No tested site
  changes the reached candidate output words. The D38E sample test replaces
  the controller stream, so neither path demonstrates simultaneous Tx/Rx.
  An [independent upper register-address screen](g2/INDEPENDENT-SLICE-ADDRESSES.md)
  also removes the unproven shared A/B-address coupling. A photo-compatible
  upper B field changes reached candidate output values, but only as a startup
  transient or another fixed value **when controller bits occupy D0**. Across
  24 and 16 reachable Q seeds in the two upper-B variants, that D0 encoding
  gives identical state traces despite 128 nominally selected input bytes.
  The [D-lane correction](g2/INDEPENDENT-SLICE-D-LANES.md) finds that D4–D6
  instead change the `39E` ALU result one loop later under the upper-B
  variant. Keep the actual D-bus lane and DAC clock open; this bounded bit
  forwarding is still not a transmitter.
  A [U8 instruction sensitivity screen](g2/UPPER-I-FIELD-SENSITIVITY.md)
  exposes a duplicated U18.6 source in the translated upper field: it
  supplies both U8 I2 and I7 without a traced fan-out. Replacing either
  source with any other direct U18 bit removes the D4→`39E` pulse effect;
  some replacements stop selecting D altogether. A single I0 polarity flip
  raises selected ROM reads to 390 and changes three pulse-dependent ROM
  addresses, but state reconverges within two input checkpoints and `39E`
  stays fixed. Treat the earlier D-lane byte rule as conditional on these
  unresolved instruction nets, and score future mappings by retained signal
  behavior rather than read count.
  The [upper-I0 ROM liveness screen](g2/UPPER-I0-ROM-LIVENESS.md) now tests
  that polarity variant over all 256 initial Q bytes with D4 held low/high.
  The 32 Q values that repeatedly enter `389–3A1` all settle to one Y byte
  at every loop site and one ROM address/byte at each read site after eight
  visits. Independent A8 choices at `389/38A/38C` change some static levels
  but not that plateau. The earlier 19–25 distinct addresses per full run
  are startup activity, not a sustained ROM oscillator. Seek a different
  phase-retaining mapping or output path; these untraced nets are not blockers.
  A [lower instruction source screen](g2/LOWER-I-INPUT-PIPELINE.md) tests
  U11 bits 0–7 as U2 I2 or I7. The D4→`39E` one-visit relay survives every
  direct source choice, so the lower U11.6 duplicate is not necessary for
  that relay. U11.0 or U11.4 at U2 I2 instead carries a pulse through four
  loop-boundary states and gives exact two-visit delayed ALU bytes at `38F`
  and `3A1` under the real controller bitstream. ROM addresses do not change
  and the candidate output still relays one bit; constrain U2 I2 and keep
  looking for a sustained ROM-using and DAC-bound path.
  The [dual-input byte screen](g2/DUAL-INPUT-ADC-NIBBLE.md) uses the same two
  lower-field candidates to offer every byte at the newly selected D3A1
  site while controller bits continue at D38E. Both inputs are selected;
  D3A1 updates R7 as `60 | ((0B + (D & 0F)) & 0F)` for all 256 bytes.
  Every next-boundary state, ROM address and candidate output matches the
  zero-byte control. This is a concrete simultaneous-ingress computation,
  but it does not yet retain a sample or recover a receive bit.
  A [single lower-instruction pin screen](g2/LOWER-I-ADC-RETENTION-SCREEN.md)
  tries all 72 direct U11 source substitutions. Five select both D3A1 and
  D38E through the comparison window; D3A1 bytes `01`, `80` and `FF` yield
  no later retained state, ROM-address change or candidate output change in
  any of the five. The next receiver search needs a joint field/timing or
  different state-path hypothesis, still without waiting for pin tracing.
  A [follow-up on the divergent lower-I paths](g2/LOWER-I-BRANCH-FOLLOWUP.md)
  finds two repeated one-bit ALU relays at `396/398` or `39A/39C`, plus a
  separate `3ED–3FA` loop that cycles eight quarter-sine ROM addresses at
  `3F7`. D38E is absent from that ROM loop; a byte at its selected D3F8 site
  also lasts just one boundary. Test a photo-compatible way for the ROM values
  to reach controller-driven state and a DAC latch; the loop alone is not a
  carrier-output proof.
  A [paired-bank and single-byte 3F7 check](g2/LOWER-I-ROM-DATAFLOW.md) then
  shows where those selected table bytes go: they update R10, the only RAM
  location affected by a 3F7-only A8 bank change across 1,580 cycles. ALU Y,
  flags, Q and PC path stay equal; one changed ROM byte is overwritten at the
  next `3F7` visit. The next mapping/timing candidate must carry R10 or the
  table byte into a later output or decision path.
  A [same-net E4/E2 phase candidate](g2/LOWER-I-ADDRESS-PHASE.md) does carry
  the `3F7` table byte into later ALU values and a branch: changing only the
  21st upper-bank byte `44→33` changes `3F9` Y and sends `3ED` to `3EE`
  instead of `3EA`. This requires I7/A0 and I0/A1 to take `0/1` together at
  `3F9/3FA`, with `1/0` elsewhere; the clock and levels are untraced.
  Its upper-bank run makes 59 selected `3F7` reads and changing internal Y
  values, but D38E is absent and no DAC sample is established. Constrain the
  timing and output continuation without treating the missing trace as a
  blocker.
  The E4/E2 phase schedule disables U10/U11 at `3F9/3FA` in the same phase,
  so that result needs an additional held-output circuit to be physical.
  A [read-valid PROM-data source screen](g2/LOWER-I-PROM-DATA-ROUTE.md) instead
  tests four paired data-bit alternatives with U10 E2 low and U11 E4 high.
  Inverted U10 D6 for I7/A0 and U11 D2 for I0/A1 keeps 59 upper-bank `3F7`
  reads, makes changing Y at `3F8–3FA`, and a single `44→33` byte change
  sends `3ED` to `3EE` rather than `3EA`. Those source and inverter routes
  remain untraced; no controller-fed or DAC-bound waveform is shown.
  A [selected D3F8 input screen](g2/LOWER-I-D3F8-INPUT.md) now offers bytes
  at the repeated D sites of that mapping. D1–D3 impulses at the 21st D3F8
  visit persist across 5–14 loop boundaries, change later selected ROM
  addresses and eventually branch away. Constant high bits keep the loop;
  actual 8031 bits offered there exit after 28/38/53 visits, short of a
  sustained transmitter. D3FA D1 affects one ALU site without a ROM/PC
  change, and D3EB single-bit controls have no modeled effect. Determine
  which physical input and clock could feed D3F8, then test for a recovered
  decision or DAC-bound stream rather than treating these state changes as
  proof of either function.
  A [D3F8 schedule screen](g2/LOWER-I-STREAM-SCHEDULE.md) tests all 256 Q
  seeds with one real 8031 bit per visit, plus 2/4/8/16-visit bit holds for
  Q=`00–0F`; none consumes the full 128-bit stream. A reference ADC-like
  waveform under every forward cyclic start position at Q=5 also exits
  before 128 samples (at most 121 or 98 visits for the two byte polarities).
  A time-reversed control survives 133 visits, showing ordering sensitivity
  but not a physical receiver. Change the input mapping/timing hypothesis
  or follow an independent signal path; these fixtures do not meet C2/C3.
  The [held D3F8 history test](g2/LOWER-I-D3F8-HELD-HISTORY.md) now uses
  the loop's measured eight-instruction visit spacing and a 9,600 Hz
  candidate sample schedule of alternating 188/187 visits at `k=1`. Among
  64 biased odd-nibble transitions, 28 remain on the same long PC path as
  their steady later-byte controls and 19 retain different final states.
  In the `01→03` versus steady-`03` witness, both receive the same byte
  from visit 188 and reach 745 selected visits, yet differ through visit
  744, including 1,034/1,112 later ROM-address events. This is persistent
  internal input history under a labelled D3F8 mapping, not a decoded ADC
  waveform or USART receive bit. The [ADC-bit decoder screen and order
  witness](g2/LOWER-I-D3F8-ADC-DECODER.md) now feed 32 consecutive reference
  complementary ADC codes through explicit two-level D3F8 hypotheses with
  188/187-visit sample holds. Eight of 112 bit/polarity/code-pair cases reach
  all 6,000 visits. In detailed `03/05` tests, bits 0 and 4 select all 6,750
  input visits and retain different state at all 750 visits of an identical
  four-sample tail after the earlier waveform is reversed; bit 6 selects the
  same number but loses the order difference. The changed later ROM addresses
  and ALU Y values are conditional receive-side leads, not recovered bits.
  The follow-up [cross-symbol screen](g2/LOWER-I-D3F8-ADC-DECODER.md)
  challenges those eight cases with six four-dibit patterns. Only the
  original pattern keeps all eight for 32 samples; `03/05` bit 0 survives
  four patterns, but all four extended 128-sample runs leave D3F8 after
  6,002–10,690 of 24,000 scheduled visits and settle in `1E9/1EA`.
  This fixture has not demonstrated a continuing receiver. Change a
  concrete timing, input-route or field hypothesis and seek a decision
  event correlated with known dibits across sequences and phases; keep C3
  open without blocking on the untraced ADC bus.
  A [uniform select-0 condition screen and sign follow-up](g2/LOWER-I-D3F8-SIGN-ADC.md)
  make that next change: inverted sign, with either flag timing, keeps all
  six tested 128-sample ADC-bit streams in D3F8 for 24,000 visits each.
  The independent reference receiver recovers the test dibits; detailed
  real-PROM traces for two patterns select all offered D3F8 bytes on the
  same PC path yet differ at 5,259 state boundaries and 10,072 selected
  ROM-address events. This is a stronger conditional input-processing path,
  not a recovered bit. Inspect symbol-timed register/ALU events and test a
  candidate decision route to USART-01 RxD; C3 remains open.
  The [symbol-bit screen](g2/LOWER-I-D3F8-SYMBOL-BIT.md) checks every fixed
  phase of the 1,500-visit symbol, both polarities and five symbol lags for
  direct bits of Y at `3F8/3F9/3FA`, Q and all 16 RAM bytes. Across three
  training and three holdout patterns, neither dibit bit has an exact
  training fit (minimum 1/36 and 3/36 errors). Input-sensitive state is
  therefore not yet a decoded symbol. A [symbol-to-symbol XOR/subtraction
  screen](g2/LOWER-I-D3F8-SYMBOL-BIT.md) also finds no exact training fit:
  XOR minima are 6/36 and 7/36 errors, subtraction minima 1/36 and 3/36;
  the selected close subtraction fits make 10/36 and 14/36 holdout errors.
  Test a constrained two-bit or multiword decision and its candidate output
  route; do not mark C3 complete.
  A [held full-ADC-code test](g2/LOWER-I-D3F8-FULL-ADC.md) now offers raw
  complementary sample bytes to D3F8. Six periodic and four nonperiodic
  128-sample streams all sustain 24,000 visits under inverted previous sign,
  even with D0 low for many samples. Two detailed streams select every
  offered byte and change modeled state with the waveform. Crucially,
  masking **ADC bits 4–7** while preserving the low nibble gives identical
  full traces for both: this mapping has not demonstrated an 8-bit receive
  datapath. Change a photo-compatible upper-slice/latch route or test a
  low-nibble decision against independent dibits; C3 remains open.
  The [upper-D instruction-source test](g2/LOWER-I-D3F8-UPPER-D-ROUTE.md)
  makes that one-bit mapping change: U8 I0 from U17 bit 5 to bit 6 changes
  D3F8's upper instruction `FC→FD`, selecting the external high D nibble.
  Ten periodic/nonperiodic 128-sample streams sustain 24,000 visits each.
  In two detailed full-versus-masked comparisons, the same PC path now
  retains upper-nibble effects at 5,812/6,000 state boundaries and more
  than 11,000 selected ROM addresses, while the baseline has zero effects.
  This is a strong **conditional** input-path candidate; the U17-to-U8 wire,
  ADC bus and receive decision are untraced. Seek a symbol decision and a
  path to USART-01 RxD before claiming C3.
  The [upper-sensitive symbol screen](g2/LOWER-I-D3F8-UPPER-SYMBOL.md)
  then checks all 1,500 fixed phases per symbol for direct Y/Q/RAM bits and
  same-byte symbol-to-symbol subtraction bits against three training,
  three periodic holdout and four nonperiodic holdout streams. No tested
  rule exactly fits even the 36 training symbols (direct minima 1/36 and
  2/36 errors; subtraction 3/36 and 2/36). This rules out only that simple
  readout family under the stated candidate mapping. Infer a constrained
  decision from instruction behavior and test it across the independent
  streams and a candidate RxD output route; C3 stays open.
  The [D3F8 lookup-chain trace](g2/LOWER-I-D3F8-LOOKUP-CHAIN.md) now gives
  that candidate's first concrete computation: upper `FD` XNORs the offered
  ADC high nibble with pre-existing RAM[A] high nibble, and `3F9` reads the
  real Am27S31 at `0x100 + Y`. Both equations hold on all 512 visits in
  each of two waveform runs. Full versus high-nibble-masked bytes change
  324/512 next ROM addresses with `FD`, versus none with baseline `FC`.
  Follow the table byte through the rest of the loop and test a constrained
  decision on independent streams; this is still conditional dataflow, not C3.
  A [3F9 ROM-byte replay](g2/LOWER-I-D3F8-ROM-FEEDBACK.md) then verifies on
  512 real-PROM visits that lower instruction `15` writes the table-derived
  low nibble into Q and upper `ED` computes a masked high-nibble RAM write.
  Replaying all fetched bytes reproduces the trace; toggling one ROM D0 bit
  at visit 20 changes 491 subsequent state boundaries and 492 `3F7` lookup
  addresses without changing the PC path. A ROM D4 toggle at that visit is
  masked by the current high-slice state. This shows conditional lookup
  feedback, while receive-bit identification and USART routing remain open.
  A [small-codebook receive screen](g2/LOWER-I-D3F8-UPPER-CODEBOOK.md)
  tests 20 reached state bytes at every fixed symbol phase, with direct,
  XOR and subtraction readouts against a prior symbol. Learned four-way
  lookups with at most 4, 8 or 16 byte values have no exact fit even on
  48 training symbols from periodic and nonperiodic reference streams;
  separate holdouts also fail. The table/Q feedback is therefore not a
  demonstrated single-byte dibit decision in this fixture. Seek a constrained
  multiword or differently clocked output and its USART-01 RxD route.
  A [held-byte classification](g2/LOWER-I-HELD-NIBBLE-CYCLES.md) finds that
  only D3F8's low nibble affects this candidate loop: all 16 high-nibble
  choices share one full trace. Ten low nibbles sustain exact recurring
  ROM-address, ROM-byte and `3F8–3FA` ALU periods of 2–21 visits; six exit.
  A [two-nibble controller screen](g2/LOWER-I-NIBBLE-STREAM-BRIDGE.md) then
  finds three of 90 zero/one encodings (`5/3`, `7/8`, `F/2`) that consume all
  128 locally executed 8031 scrambler bits and change repeated ROM/ALU
  values. They require an untraced multi-bit D3F8 source and one new bit
  every eight microcycles. All three exit early with 2/4/8/16-visit holds;
  this is an internal algorithmic lead, not a timed 1,200-baud connection or
  DAC output. Test a physically plausible input phase and output latch next.
  A [clock-matched D0 replay](g2/LOWER-I-TIMED-D0-STREAM.md) finds a simpler
  single-bit continuation: hold D3F8 D3 high, D2/D1 low, and put the 8031
  bit on D0 (`08/09`, or its inverse). With 750 loop visits per bit, exactly
  the `14.4 MHz`, `k=1`, 2,400 bit/s hypothesis for this eight-cycle loop,
  both polarities select all 96,000 offered D3F8 bytes and continue through
  the full 128-bit stream. The first bit change alters `3F8–3FA` Y and later
  `3F7` ROM addresses. The exact alternating 187/188-visit `k=4` schedule
  and fixed 250/375-visit `k=3/2` schedules exit early. This is a strong
  internal controller-to-ROM execution witness, conditional on the untraced
  input connection, clock and PROM-latch routes; C2 still needs a DAC-bound
  waveform and dibit/2100 Hz behavior.
  A [divided DAC-latch screen](g2/LOWER-I-DAC-SAMPLE-CLOCK-SCREEN.md) tests
  the simplest output continuation for that witness: ALU Y at `3F8/3F9/3FA`
  or `3F7`-written R10 into the adjacent 74LS273, sampled at 9,600 Hz
  under all 188 integer clock phases. Both held input levels yield exact
  four- or eight-sample cycles at every tested source; none has a 1,800 Hz
  full-byte peak, and none of eight possible D4 source bits gives the
  photo-candidate DAC08 B5 a 1,800 Hz peak under both levels. This rules
  out those **direct** latch fixtures, while a staged data path, other
  clock/source or mapping remains open without waiting for pin traces.
  The [all-live-nibble continuation](g2/LOWER-I-LIVE-NIBBLE-DAC-SPECTRUM.md)
  extends that direct-latch test to every one of the ten D3F8 levels that
  sustains the ROM loop, both 187/188 sample-clock orderings, 188 offsets,
  and all four candidate data bytes. No full-byte or photo-candidate B5
  window has a 1,800 Hz peak. A few 32-sample windows show a 2,100 Hz bin
  for held `3`/`7`, but their exact 14-sample cycle has a dominant third
  harmonic at 2,057.14 Hz. This prunes the tested direct byte routes;
  constrain the output latch data/clock or seek another mapped signal path.
  The [four/eight-visit stream screen](g2/LOWER-I-FOUR-SAMPLE-BIT-SCREEN.md)
  tests all 90 ordered live-nibble pairs with 128 real controller bits. None
  survives four visits per bit; at eight visits, D0-only `08/09` alone
  consumes all 1,024 offered inputs and changes ROM/ALU state. A hypothetical
  19,200-visit/s loop permits a 9,600 Hz latch clock every second visit, but
  its 153.6 kHz microcycle and data/latch wiring are unmeasured. Screen the
  alternating-visit latch bytes and phase next, without waiting for a pin
  trace or treating this internal path as proof of C2.
  The [alternating-visit latch screen](g2/LOWER-I-ALTERNATE-VISIT-LATCH.md)
  runs that test at 9,600 samples/s, both phases and six direct Y/R10/ROM
  byte sources. Held `08` gives a constant byte for all twelve cases, so none can
  provide its steady 1,800 Hz carrier. A short controller-stream window at
  three source/phase cases have a 1,800 Hz peak, but the held controls fail. This
  closes those direct source/clock fixtures; continue with a staged latch
  route, different clock or command-dependent input rather than waiting for
  a pin trace.
  An [exit-path comparison](g2/LOWER-I-EXIT-PATH.md) follows the D3F8-sensitive
  branch: under previous-flag timing, `3FA` zero releases `3ED`, `3EE` returns
  to `18D`, and all six impulse/controller cases eventually repeat `1E9/1EA`
  with Q=0 and no selected D read or virtual output capture. Under current-flag
  timing, the loop exits after two D3F8 visits even with constant input;
  controller-lane traces match the constant control exactly. Treat these as
  timing-specific results. `3ED` and `1EA` are the same raw microword and
  condition select, so a fixed condition circuit cannot assign them different
  flag timings based on the word alone. Try another plausible mapping,
  initial state or input route rather than treating the missing physical
  trace as a blocker.
  A [later-byte relay](g2/LOWER-I-LATE-BYTE-RELAY.md) now follows one such
  alternative: previous-carry select 0 plus a labelled D3F8 pulse enters a
  repeated `3A2–3B6` path. With the real 8031 stream offered at D3A6, all
  128 bits are reflected in the internal `3B3–3B6` capture quartet according to a
  verified low-nibble rule, checked also for all 256 constant byte values.
  This is a reproducible controller-to-internal-data bridge, but the input
  connection, virtual captures and DAC route remain untraced, and the quartet
  does not establish carrier samples. Test a photo-compatible DAC latch and
  timing continuation or another state/input mapping before claiming C2.
  A [direct-clock screen](g2/LOWER-I-LATE-DAC-CLOCK.md) now replays the
  photographed DAC08 B5←LS273 Q4 candidate with all eight untraced Y-bit
  sources and every fixed clock subset of `3B3–3B6`. Both constant-symbol
  controls repeat a pattern of at most four captured codes, so none of these
  direct clocks can supply an 1800 Hz carrier at the hypothesised 9600 Hz
  sample rate. All 137 complete PC/Y blocks of the enclosing 12-word loop
  also repeat under each constant control, extending that exclusion to any
  fixed set of direct clock sites within the loop at this cadence. A
  held-data stage, another path or sample rate remains open; the photo does
  not trace the LS273 clock or full DAC byte wiring.
  A [two-input late-loop run](g2/LOWER-I-COMMAND-DATA-MIX.md) now combines
  frame lane 1 with USART-01 bits from four uninterrupted 8031 main-loop
  classes, under separate assumed D3A4/D3A6 routes. Every one of their
  64/64/48/48 line bits follows the exact executed quartet rule
  `(F0|n, F0|((m+n)&0F), n, 0F-n)`, where m is the frame byte's low nibble
  and n is the line input's low nibble. A 224-bit diagnostic concatenation
  preserves this rule, and switching only frame lane 1 `47→42` changes only
  the second captured Y on all 64 common-line visits. This is a conditional
  command/data arithmetic bridge, not DAC-bound modulation; the artificial
  entry trigger and both input connections still need independent support.
  A [direct LS273 clock replay](g2/SPLIT-DAC-CLOCK-SCREEN.md) holds each
  controller bit for eight loop visits and samples ALU Y at `38E` or `39E`.
  Both candidate clocks yield constant codes under constant-symbol controls,
  and neither meets the carrier-sample test. This narrows those explicit
  output scenarios without requiring a complete pin trace.
  A [front-photo upper-bundle screen](g2/PHOTO-UPPER-BUNDLE.md) now highlights
  U17/U18-to-U29/U30 track candidates and tests all 24 orders of U18 bits
  4–7 as the upper B field. Every order keeps reached `39E`/`39F` output
  fixed under D4 zero/one, although internal state responds. The U30-to-U8
  continuation is untraced, so this prunes a tested field family rather than
  proving the earlier low-bit field or blocking further runs.
  A [full-byte replay](g2/SPLIT-FRAME-BYTE-RULE.md) then classifies the
  earlier low-bit upper-B fixture exactly: after startup, `39E` equals
  `1B + 2*(previous D38E byte & 70)` for all 256 byte values in both orders
  and for four real 8031 frame streams. That loop relays selected byte bits
  with one-visit delay and reads one fixed ROM address; it is not the
  advancing modulator or receiver needed for G2 under these assumptions.
  Neither the arithmetic identity nor the short dibit run is a transmitter.
  An [A8 bank screen](g2/SPLIT-ROM-BANK-SCREEN.md)
  varies global and `38C` bank choices across the same six streams. The ROM
  operand and internal state change, but the exact `39E` byte rule survives
  all 24 runs. A8 alone does not yield a ROM-shaped output at this site;
  continue with another retained ROM path and a timed latch hypothesis.
  A [receiver Q-seed screen](g2/RECEIVER-SEED-RETENTION.md) then tests five
  one-byte ADC-like impulses at the selected `38E` or `3A1` D site in three
  slice layouts. Among 32, 32 and 24 Q seeds that reach the candidate input
  repeatedly, none retains an impulse in the modeled state at cycle 1,024.
  The upper-B candidate shows a two-boundary transient, so its input path is
  real within that fixture but still lacks receiver history. Seek a separate
  command/sample ingress or another branch and retained-state path.
  The [held ADC sample replay](g2/ADC-38E-HELD-SAMPLES.md) corrects the
  earlier per-visit conversion schedule: under a 14.4 MHz/9,600-sample/s
  hypothesis, each complementary byte stays at D38E for 125 visits. Two
  reference-waveform histories converge to the same full modeled state at
  their first shared input group, with no recurring selected ROM read.
  This closes that q3/Q=5 ingress under held-sample timing, not the ADC
  receiver or another mapping.
  A [separate held D3A1 replay](g2/ADC-3A1-HELD-DUAL-INPUT.md) keeps real
  8031 line bits on D38E at 500 visits/bit while complementary ADC codes
  occupy D3A1 for 125 visits/sample. Both U11.0 and U11.4 instruction
  candidates select all inputs but lose the ADC history at the first shared
  sample; reached output events and ROM addresses do not depend on that
  history. Seek a different retaining input phase or program path for C3.
  A [joint lower-I2/I7 source screen](g2/RECEIVER-JOINT-I2-I7-SCREEN.md)
  now tests 64 two-pin U11 assignments with simultaneous D38E controller
  bits and a D3A1 candidate ADC byte. Forty mappings select both inputs
  through the sample; `01` and `FF` affect only its current boundary, while
  none of the tested bytes changes a later state, selected ROM address or
  candidate output event. The other 24 mappings do not support a retention
  conclusion. This narrows the two-pin variant of the `389–3A1` receive
  fixture; seek a different program path or jointly changed address/sample
  timing rather than waiting for physical continuity. C3 remains open.

  A [fast-gated full-byte screen](g2/PHOTO-127-FULL-BYTE-GATE.md) follows
  the alternative PC129 phase loop and tests selected upper-ROM bytes as
  candidate DAC latch data. Its executed 740-read recurrence supports a
  projected 9,600 Hz sample series. The raw ROM byte peaks at 3,000 Hz for
  both proposed 1,800/2,100 Hz step values; a hypothetical high-bit
  inversion produces the target peak bins but explains under half the code
  variance. The phase ramp alone has comparable or stronger target-bin
  power. Continue by finding a decoded quarter-wave or other retained
  ROM-to-latch data path and controller-selected phase steps; the pin route
  remains an assumption, not a blocker.
  A [controller-frame step check](g2/PHOTO-12C-CONTROLLER-FRAME-STEPS.md)
  tests all six distinct bytes in the executed 8031 four-byte frames as
  held D12C inputs. Four even bytes sustain the second ROM loop and two odd
  bytes exit; none supplies the exact ±48/±56 sampled phase step for
  1,800/2,100 Hz at the tested integer clock ratios. This prunes a direct
  frame-lane-to-phase-step connection without excluding a decoded or
  changing controller input or identifying the DAC route.
  A [joint frame/line execution](g2/PHOTO-127-FRAME-LINE-JOINT.md) then
  offers the real 8031 main-loop frame lane 1 at D127 and its USART bits at
  D12C. Under q3, held `47` enters the second phase loop after 155 first-
  loop ROM reads and consumes the bits; held `42` stays in the first loop
  for 1,040 reads and consumes none. At eight visits per bit, the `20`
  selector stream drives phase to zero and exits to `084`, while `00`
  consumes all 64 bits and continues. This is a conditional controller-
  driven phase/control witness under two untraced input routes, with no
  DAC-bound byte or receiver result yet.
  The [line-rate hold replay](g2/PHOTO-127-LINE-RATE-HOLDS.md) tests that
  direct serial-bit route at `1500/k` PC12C visits per 2,400 bit/s bit for
  `k=1…4` oscillator periods/microinstruction. Selector `00` holds its
  first zero bit at one ROM address and exits during the second bit;
  selector `20` exits during its first one bit; `40`/`60` never enter PC12C.
  The earlier short-hold branch witness therefore does not show a sustained
  transmitter at the proposed physical timing. Seek a decoded/biased input
  or another stateful path without treating the missing pin trace as a
  goal blocker.
  The [four-CD4094 order model](g2/PHOTO-CD4094-ORDER.md) connects the
  executed four-byte 8031 send to the photographed shift-register capacity.
  Under a simple LSB-first cascade, the physical logical-chip order is the
  reverse of SBUF byte order, and a Q1→D0 bus also reverses bit order.
  Executed q3 D127 runs for all 20 resulting candidate bytes show that the
  earlier `47`/`42` branch split survives only one tested chip/Q orientation;
  another yields the opposite split. Keep these distinct wiring candidates
  live while testing a DAC-bound path.
  The [joined CD4094/frame/line replay](g2/PHOTO-CD4094-FRAME-LINE-JOINT.md)
  executes all eight chip/Q orientations for four controller frame and USART
  classes. Sixteen of 32 cases enter D12C, four leave at `084` during the
  diagnostic eight-visit hold, and none reaches `392`/`39E`. Chip 2 Q8→D0
  alone reproduces the literal `47`/`42` split; chip 0 Q1→D0 reverses it.
  The hold is not physical line-rate timing, so test a decoded or qualified
  input and a sustained output consumer without selecting a physical lane
  from this control-flow result alone.
  A [paired A0/A1 CD4094 replay](g2/PHOTO-CD4094-STATE-TONE.md) now tests
  logical chip 1 as the D127 control byte and another chip as held D12C.
  Q8→D0 presents A0=`88` (first loop) and A1=`81` (second loop), so this
  candidate wiring does give an executed state-dependent branch. Its three
  alternate-chip D12C bytes are even and sustain the A1 loop, but none gives
  the required ±56 phase step for a 2,100 Hz tone at the tested 9,600 Hz
  gate and clock divisors. A decoded step and DAC-bound consumer remain to
  be demonstrated; the A1 tone interpretation is still provisional.
  The [controller P1 replay](g2/CONTROLLER-STATE-PIN-CHANNELS.md) exposes a
  second command channel: A0 and A2 transmit the same four-byte frame, but
  the executed send routine leaves P1.5 high for A0 and low for A2. A1 is
  also low. Include this pin as an independent candidate control input when
  testing state-dependent DSP behavior; its physical destination and tone
  meaning are not established.
  A [paired-bank second-loop replay](g2/PHOTO-12C-ROM-LIVENESS.md) now shows
  that changing the selected Am27S31 bank at `12E` changes hundreds of ALU
  bytes and some `12F` results, yet every complete post-`12D` state agrees
  across banks for four held phase inputs. In this q3 fixture, any DAC route
  using the ROM shape must sample `12E`, `12F` or the following preclear
  `12C` window; a later state consumer cannot recover it. Test a qualified
  latch clock in that window under explicit chip/timing assumptions.
  The [A0/A1 PROM-edge screen](g2/PHOTO-12C-PROM-EDGE-LATCH.md) finds one
  raw rising bit, U18 D1, that fires at all 613 A1 `12E` visits and never
  in the recurring A0 first loop for three held CD4094 phase bytes. If it
  clocked a Y-fed latch, A1 would produce changing codes, but the edge runs
  at 0.9–3.6 MHz under the tested fast-clock ratios. U18 D1 is also a
  tentative register-address bit. Test a photo-compatible divided/qualified
  clock and full DAC byte route before assigning output function.
  The [divided-strobe replay](g2/PHOTO-12C-DIVIDED-STATE-LATCH.md) performs
  that first clock test at 9,600 captures/s for the three held alternate-chip
  A1 bytes. Full `12E`/`12F` Y and the candidate DAC B5 bit peak away from
  2,100 Hz for the integer clock ratios. The fractional ratios at oscillator
  divisors 2 and 4 also fail the target-bin peak bound across all divider
  alignments. A direct held byte cannot supply the proposed A1 tone at
  9,600 captures/s in these divisor-1–4 fixtures. Next test a decoded or
  changing D12C phase step and
  a constrained full DAC byte path, rather than treating the missing net as
  a goal blocker.
  A [two-wire CD4094 permutation](g2/PHOTO-CD4094-BIT-SWAP-TONE.md) is a
  concrete alternative: swapping candidate D0/D3 before D127 makes the
  executed A1 `81→88` stay in the PC129 loop, while A0/A2 `88→81` enter
  PC12E. At the divisor-1, 9,600-sample/s gate, A1's projected full Y and
  photo-candidate B5 both peak at 2,100 Hz across all start phases. This is
  an untraced two-wire route and a spectral witness, not a DAC waveform.
  All 11 raw PROM edges aligned with A1 PC129 also fire at every A0 PC12E;
  test a photo-compatible qualified latch and full-byte output route before
  assigning the loop a transmitter function.
  The [bit-swap data-site screen](g2/PHOTO-CD4094-BIT-SWAP-DATA-SITES.md)
  compares the executed phase, ROM byte and `129/12A` ALU values as possible
  full DAC bytes. At divisor 1, the upper-bank ROM byte peaks at 3,000 Hz;
  `129` Y peaks at 2,100 Hz but puts only 0.346 of its variance there, while
  `12A` Y reaches 0.609 mainly because it is the raw phase ramp plus a
  carry bit. This is a tone-rate internal walk, not yet a sine DAC code.
  Look for a constrained shaping/latch route or a better mapped output
  source; do not infer one from the single B5-bit peak.
  A [photo-B5-compatible DAC bus screen](g2/PHOTO-DAC08-BUS-ORDER-SCREEN.md)
  tests reverse, one-position rotation and Q4/Q5 exchange as full LS273-Q
  to DAC08-B orders, with ordered or Y7/Y4-swapped ALU-Y inputs. All preserve
  the candidate Q4→B5 photo segment. If Y7 drives Q4, B5 peaks at 2,100 Hz
  but **none** of the three `129` full-byte codes does; only the reversed
  `12A` code retains that peak, with 0.247 target-bin variance fraction.
  The remaining DAC pins and clock are untraced. Use full-byte and physical
  constraints together when testing further output routes.
  A [main-frame carrier swap](g2/PHOTO-MAIN-FRAME-CARRIER-SWAP.md) finds a
  more direct data-state lead: all four ROM-executed 8031 main-loop frame
  classes place `A1` on candidate logical CD4094 chip 1. A single D0/D4
  crossing, unique among pairwise swaps to an exact 1,800 Hz step, presents
  D127=`B0`. Four 3,000-word real-PROM runs sustain 740 PC129 reads. With
  upper-bank ROM and divisor-1 9,600 Hz gating, both `129` Y and a minimal
  photo-B5-compatible full DAC bus peak at 1,800 Hz; the full code's target
  fraction is 0.604. Lower bank and divisor 3 fail. This is a controller
  **frame** to carrier-rate witness under untraced wiring, not USART dibit
  modulation. Next test line-rate phase changes and the DAC clock separately.
  The [line-rate held-bit replay](g2/PHOTO-MAIN-FRAME-LINE-HOLD.md) now overlays
  real ROM-executed USART-01 bits on D127 D4 or D5 for the 1,500 loop visits
  per 2,400-bit/s bit under the divisor-1 hypothesis. All eight controller
  class/lane runs preserve the loop and accumulate the expected 64- or
  128-step phase difference after a one bit, but the candidate full DAC-code
  peak moves from 1,800 Hz to 3,600 or 600 Hz during that held level. This
  direct gate is a frequency-excursion fixture, not yet the required dibit
  phase modulator. Seek a photo-compatible symbol-boundary or decoded input
  timing rule; do not insert ideal kicks as if they were recovered wiring.
  A [counter/parity pulse screen](g2/PHOTO-MAIN-DIBIT-PULSE.md) now tests one
  such explicitly hypothetical rule: four PC127 visits per 1,200-symbol/s
  dibit, with U1 parity and U24 counter roles suggested only by photographed
  part markings. Four real USART streams drive 288,256–384,256-word
  uninterrupted PROM runs across all 24/32 available dibits; all four
  Gray-related phase offsets are retained, while the candidate carrier step
  resumes between pulses. The gate and DAC capture are untraced, no pulse
  shaping or line output is established, and one full-stream candidate DAC
  spectrum disagrees with the same-input reference. This is not a C2 pass.
  Constrain the pulse and output routes before assigning this the modem's
  data-transmitter function.
  A [DAC bus/independent-decode screen](g2/PHOTO-MAIN-DIBIT-DAC-DECODE.md)
  now compares six photo-B5-compatible full-byte mappings on those verified
  code streams. Ordered Y→LS273 with Q4/Q5 exchanged at DAC08 yields one
  error in 104 real dibit decisions, with zero errors on 74 decisions held
  out from bus selection; every other tested order makes at least 31 errors.
  The decoder is a known-carrier reference tool, not the DSC receiver, and
  the pulse, DAC clock and analog route remain assumed. Keep C2 and C3/C4
  open while tracing or otherwise constraining those physical paths.
  An [exhaustive B5-compatible bus screen](g2/PHOTO-DAC-BUS-PERMUTATIONS.md)
  corrects the six-order selection claim: 12 of all 5,040 seven-bit
  permutations decode all 104 dibits, and 172 have one error. The earlier
  Q4/Q5 swap is among the latter and has lower reference-waveform
  correlation than every perfect-decision order. The signal carries
  conditional phase information, but the full DAC bus is not identified;
  constrain another bit or the latch/analog path before treating it as
  line output.
  A [nonperiodic dibit holdout](g2/PHOTO-RANDOM-DIBIT-VALIDATION.md) now
  tests those 12 fixed orders on four seeded 256-symbol streams. Two
  32-symbol prefixes are checked by full real-PROM execution, including
  every `129` address, ROM byte, Y result and candidate sample hash. The
  four longer projections score 1,016 decisions per bus: six orders stay
  error-free, the other six make 5–10 errors, and unpulsed carrier controls
  make 186–198 errors per stream. This strengthens the conditional DPSK
  behavior and fixes candidate source bits 0, 2, 4, 6 and 7 to DAC code
  bits 4, 5, 3, 6 and 7, respectively; source bits 1, 3 and 5 remain
  permutable across DAC code bits 0–2. The physical decoder, DAC latch and line
  output untraced; C2 remains open.
  A [joint data/tone screen](g2/PHOTO-DAC-JOINT-DATA-TONE.md) then keeps each
  of the 12 zero-error buses fixed through the existing A1 `B0→88` dynamic
  PROM replay. All 12 retain projected 1,800/2,100 Hz peaks across all four
  selector classes, so the candidate route is compatible with both tests
  but the tone does not choose a unique bus. The A1 decode and physical
  output remain assumptions, and C2 still needs segment-1 and line checks.
  An [extended 8031 polling-loop replay](g2/MAIN-LOOP-LONG.md) now supplies a
  real controller frame toggle to test a phase-control hypothesis: on the B4
  branch, the third frame byte alternates `81`/`C1` every four forced-timer
  iterations, while the A5 branch has a shorter toggle. Replay that observed
  sequence with the real line-side bytes through labelled held-frame and DAC
  routes, and compare against a fixed-bit control. The forced iterations do
  not establish reversal timing or the physical destination of frame bit 6.
  The first [held-route screen](g2/PHOTO-FRAME-TOGGLE-ROUTES.md) excludes both
  existing D127 interpretations as a carrier-preserving reversal: the mode
  decoder ignores the `81`/`C1` difference and projects 2,100 Hz for both,
  while the direct D0/D4 crossing projects 600/3,000 Hz. Test a transient
  sampling rule or another control route; keep the observed controller frame
  sequence distinct from the assumed DSC input wiring.
  A [two-visit edge-pulse replay](g2/PHOTO-FRAME-TOGGLE-EDGE-PULSE.md) now
  applies real B4 `C1→81` frames and eight actual port-01 bytes to one
  parity/counter hypothesis. Two uninterrupted 384,256-word PROM runs show
  the proposed frame-edge pulses add and then cancel a retained 128/256
  phase offset without losing the dibit stream. The edge gate, frame/byte
  timing, DAC route and B4 segment meaning remain untraced, so this is a
  conditional mechanism, not a C2 pass. Constrain one of those routes with
  independent evidence before interpreting the half-turn as Nokia output.
  The [64-iteration counter trace](g2/MAIN-LOOP-COUNTER-LONG.md) now identifies
  the controller source of that frame bit: a state-indexed ROM table reloads
  RAM49 to 32 in B4 and 8 in A5, causing eight and two bit-6 toggles at
  four-build spacing. All 256 output builds match the independent builder
  model. This is a deliberate finite controller pattern, but the forced
  polling/build cadence does not establish its physical reversal interval.
  The [segment-1 cadence check](g2/PHOTO-SEGMENT1-REPEATED-DIBIT.md) sharpens
  that limitation: V.26 ter §2.7.1 requires a 180° reversal at **each** of
  32 symbol intervals. In the tested one-byte/four-symbol alignment, B4 bit-6
  changes only at symbols 0 and 16, so its direct edge-to-D127 pulse route
  cannot produce segment 1. A separate synthetic run of 32 repeated `11`
  dibits executes 384,256 PROM microinstructions and alternates the retained
  phase offset `128/0` every symbol; all 12 surviving DAC bus projections
  decode the 30 aligned transitions as `11` with zero errors. This proves
  candidate-path capability, not a controller-sourced segment-1 run or C2.
  A [direct controller-stream screen](g2/CONTROLLER-SEGMENT1-STREAM-SCREEN.md)
  checks all four executed 64-iteration port-01 byte streams under both
  serial bit orders and dibit alignments. Their longest identical-dibit run
  is at most six symbols, so fixed two-lane swaps/inversions cannot turn
  those scrambled writes into the 32 repeated `11` dibits of segment 1.
  This narrows the direct-port-01 hypothesis only; the pre-scrambler source,
  DSP-side generation/descrambling, state commands and untested timings stay
  open.
  The [standard-pattern PROM calibration](g2/PHOTO-SEGMENT2-STANDARD-CALIBRATION.md)
  then drives the real A4/A5 64-bit GPC and GPA streams through two candidate
  four-visit D127 pulse-lane orders. Four 384,256-word PROM runs check 96,054
  PC129 ROM/ALU events each. Exchanging the two serial-bit lanes yields zero
  errors in 30 aligned **standard-labelled** phase decisions for each pattern
  on all 12 surviving DAC buses; the original lane order gives 6/8 errors.
  This corrects the earlier first-bit-low numeric dibit convention: its
  104-decision zero-error screen was not itself a V.26 ter bit-order check.
  The controller supplies a real standard synchronization pattern, and the
  candidate DSC path can modulate it with an explicit lane swap, but the
  pulse circuit, DAC latch, full bus, line output and natural schedule are
  still assumptions. C2 is not yet passed.
  Seek the actual segment-1 source or an independently supported control
  route without treating unknown nets as a blocker.
  A [joint state/data wiring check](g2/PHOTO-STATE-DATA-BUS-COMPATIBILITY.md)
  now prevents combining the two separate bit-swap leads as one fixed
  chip-1 connection. The ROM-executed A1-state `81` and main-frame `A1`
  differ by one bit, whereas every exact 2,100/1,800 Hz D127 step pair for
  divisors 1/3 differs by at least two. Fixed pin permutations and fixed
  inversions preserve Hamming distance. Cross-replaying both candidates
  confirms D0/D3 gives 2,100 Hz in A1 but 900 Hz in main data, while D0/D4
  gives 1,800 Hz in main data but 600 Hz in A1. Treat each as a diagnostic
  route; seek a mode-dependent selector, different source or other output
  path without promoting either simple crossing to board wiring.
  A [small fan-out/inversion decode](g2/PHOTO-CONTROLLER-MODE-DECODE.md)
  can map isolated A1 `81→88` and first-line main `A1→B0` while using raw
  bit 0 as a hypothetical output gate. The real-PROM replay gives the
  candidate 2,100/1,800 Hz full-code peaks. **But** the preserved 8031
  main-loop chain sends `80 02 A1 7A` in all 512 tested A1 sends, rather
  than isolated fixture's `80 02 81 7A`. The same decode would select the
  1,800 Hz branch already in A1. Controller output32 bit 5 is a counter-phase
  flag, not a state-only mode bit. Treat A1 tone semantics and this decoder
  as unresolved; trace the counter phase and actual frame chronology before
  promoting either spectrum to the physical operating sequence.
  The [joined tone/training/data replay](g2/PHOTO-JOINT-TONE-TRAINING-DATA.md)
  now uses that chronology: after 11 early `A1` frames, the Timer-1-paced
  controller emits `81` once and predominantly `C1` in A1. A fixed,
  **assumed** decode of the third and fourth frame bytes selects D127=`88`
  for late A1, disables a candidate output gate in A2, and selects `B0` in
  A3/A4. Two uninterrupted 1,248,256-word real-PROM runs carry a 2,100 Hz
  candidate-code peak, alternating A3 carrier-relative half-turns, and the
  actual GPC/GPA segment-2 bits with 0/62 external-decoder errors across all
  12 surviving DAC bus orders. This resolves the earlier frame-chronology
  contradiction for this *candidate*, but does not prove the frame decoder,
  A2 analog silence, DAC clock/bus or line output. The tone and silence
  windows are diagnostic excerpts, not natural handshake durations. Next
  test a photo-compatible latch/output route; keep C2 open until its line
  output conditions are met, and continue C3/C4 independently.
  A [conditional line-stage screen](g2/PHOTO-JOINT-LINE-FILTER-SCREEN.md)
  now applies one A2 mid-code mute gate and a fixed 1,950 Hz biquad bandpass
  to the same hash-checked joined PROM stream. At Q=1, all six independently
  validated DAC orders in both controller modes retain the 2,100 Hz peak,
  fit it with R² 0.721–0.725, settle to less than 0.001 of tone RMS by the
  last 32 A2 samples, and decode A3/A4 at 0/62 errors with one common
  sample shift. Narrower Q=2/3 filters improve tone fit but introduce
  at least 17/70 errors across the twelve cases. This gives a useful
  analog-bandwidth and gate-timing target, not an independently constrained
  line waveform; the latch, DAC current-output and connector routes keep
  C2 open.
  The [output-clock phase screen](g2/PHOTO-JOINT-OUTPUT-CLOCK-PHASE.md)
  projects the PROM-checked recurrence through all 375 offsets of a
  hypothetical one-capture-per-375-`129`-visits gate. All offsets retain the
  candidate 2,100 Hz peak; 234 offsets give 0/62 A3→A4 errors on all 12
  buses in both modes. The frequency match is a sampled alias: `88` advances
  56 phase counts per 9,600 Hz sample and `B0` advances 208, equivalent to
  −48. At the photographed 14.4 MHz oscillator, the tested 3,000-visit
  symbol schedule implies 1,200 baud only if the four-word loop executes
  one microinstruction per oscillator period. The actual divider and DAC
  latch clock are not traced. Screen concrete clock/gate candidates; do not
  treat the many matching offsets as proof of the physical output path.
  A [free-running-clock site replay](g2/PHOTO-JOINT-FREE-CLOCK-SITES.md)
  now tests a simpler latch alternative directly against two full PROM
  traces: sample Am2901 Y every 1,500 microinstructions at `127`, `128`,
  `129` or `12A`. **All four** sites peak at 2,100 Hz in A1 and give 0/62
  A3→A4 external-decoder errors across the 12 candidate DAC buses. Their
  byte waveforms differ substantially (`R²(2100)` ranges 0.336–0.610), so
  those two signatures cannot identify the actual latch site or prove the
  `129` ROM-shaped byte is the line output. Compare output shape and the
  photographed 74LS373/74LS273 data/clock routes before closing C2.
  The [pulse-shaped waveform screen](g2/PHOTO-JOINT-WAVEFORM-SHAPE.md)
  supplies the first of those discriminators. It re-executes both full
  traces, verifies all eight site-code hashes, and fits each of 12 DAC bus
  orders at four ALU sites against the independent raised-cosine reference.
  PC129 wins for **all 12 fixed bus orders** in both GPC and GPA; its best
  mean R² is 0.757, versus 0.653 at the best other site, and its per-bus
  margin is 0.092–0.131. Several PC129 bus orders remain close, the fit is
  incomplete, and no latch/DAC route is proven. Use the shape ranking to
  focus photo-compatible 74LS373/74LS273 timing tests, not to pass C2.
  The [six-bus filter continuation](g2/PHOTO-SURVIVOR-FILTER-VALIDATION.md)
  revisits that ranking after the nonperiodic holdout: the prior best-shape
  bus is among the six rejected by independent data, so its R²≈0.757 is
  not evidence for the surviving family. A fixed one-pole smoothing rule
  raises mean shape R² from 0.654→0.705 on GPC/GPA and 0.595→0.647 on
  four random streams while preserving all 2,232 scored decisions and the
  2,100 Hz tone peak. The remaining fit gap and untraced analog/latch path
  keep C2 open; test actual component connections or another output stage.
  A [six-order DAC code comparison](g2/PHOTO-DAC-SURVIVOR-EQUIVALENCE.md)
  shows why the surviving bus orders are hard to separate by those signal
  tests: they share all upper-five-bit codes in both joined controller traces
  and differ by at most three DAC code counts at any sample. Carry their
  low-bit ambiguity through clock/output-route tests and seek an independent
  low-bit trace or precise analog capture to distinguish them; C2 stays open.
  A [joint transmitter/ADC field screen](g2/JOINT-TX-RX-MAPPING.md) checks
  whether the separate q3 DAC and independent-upper-slice ADC witnesses can
  coexist in one field map. All 32 tested lower-field combinations keep the
  receiver upper fields fixed. The high-slice A pins use the same labelled
  diagnostic levels as the low-slice A pins, correcting an unequal-address
  control fixture. All 32 complete the held `D127` loop; eleven also retain
  ADC high-nibble influence, but their `Y129` streams contain at most two
  values, versus 16 in both shared- and split-slice q3 transmitter controls. The
  current transmitter and receiver hypotheses therefore cannot simply be
  combined as one C2/C3 mapping. Test an upper-slice instruction/enable or
  output-latch alternative on both paths before assigning modem functions.
  The [joint upper-source screen](g2/JOINT-UPPER-SOURCE.md) tests one such
  alternative: inverted U17 D5 to upper I0/I7, with the other high sources
  from q3 and five disputed lower groups varied. Five of 32 fixed maps
  preserve 16 held transmitter ROM addresses and sustain 6,000 changing
  ADC visits. One map also sustains 24,000 visits on two periodic and one
  nonperiodic reference streams; masking the ADC high nibble changes 5,624
  selected ROM addresses in its 6,000-visit comparison. This is a
  conditional compatibility witness, not proof of the upper wires or a
  recovered C3/C4 decision. The [full transmit replay](g2/JOINT-UPPER-FULL-TX.md)
  then runs the *same* map for 1,248,256 microinstructions per call/answer
  selector with the controller-derived A1–A4 input sequence. Its candidate
  DAC-code hashes match the earlier q3 stream; both have a 2,100 Hz tone
  peak and 0/62 independent A3/A4 data errors. C2 is still conditional on
  the untraced latch, DAC bus and analog path. Keep G2 active and seek a
  generalizing receive decision and USART RxD/echo route on this map.
  The [full-row joint-map screen](g2/JOINT-FOUR-ROW-RETENTION-TX.md) finds
  a better fixed candidate: lower mask `04` retains ADC-dependent RAM/Q
  state after all four receive rows on 1,312/1,500 paired visits and on
  3,701–4,780/6,000 visits in four fresh nonperiodic streams. The same
  map completes both full controller-driven transmit modes with a 2,100 Hz
  A1 peak and 0/62 filtered data errors on all six candidate DAC buses.
  Its [retained-bit screen](g2/RECEIVER-MASK04-RETAINED-BIT.md) finds no
  exact direct R1/R12/Q bit or previous-symbol XOR on training data, so
  C3 and the untraced C2 physical output route remain open.
  The [joint-map PROM-edge replay](g2/JOINT-MASK04-TX-PROM-EDGE.md) now
  verifies that the same mask-`04` map has 312,054 U10 D2 rise/fall pairs
  per uninterrupted transmit mode and 832 divider-qualified samples.
  Its post-ROM byte hash matches the saved joint-map Y129 trace. Both
  latch phases peak at 2,100 Hz and give 0/372 A3/A4 decisions per
  phase across six candidate DAC buses in each mode, although all 832
  raw bytes differ between phases. Neither selected-bus hash matches the
  earlier q3 replay, and the q3 phase-shape ranking does not transfer.
  Keep the latch phase, data wiring and analog path as explicit C2
  hypotheses; the same map's receive sensitivity does not prove C3.
  The [A2 latch-gate screen](g2/CONTROLLER-A2-LATCH-GATE.md) identifies
  third-frame-byte bit 0 as the **only** held CD4094 frame bit high throughout
  A1/A3/A4 and low throughout A2 in both uninterrupted Timer 1 controller
  runs. A labelled connection to the photographed 74LS373 C/LE input would
  make it transparent while active and hold the last code in A2. The saved
  real-PROM hold case yields silence under the assumed bandpass with 0/1,488
  subsequent data-decision errors across 24 bus/phase/selector cases. The
  bit-to-LE wire, data route and shared timing remain open, so C2 does not pass.
  The [frame-latch event timing](g2/CONTROLLER-A2-LATCH-GATE-TIMING.md) makes
  the proposed A2 hold 61,938/61,772 controller ticks, or about 596/594 DAC
  samples under the stated 104:1 clock ratio. An [extended real-PROM run](g2/JOINT-MASK04-A2-LE-TIMED.md)
  executes 2,040,256 instructions per selector through 74 A2 symbols and
  releases the hold two/four samples into A3. All 72 bus/phase/release cases
  retain a 2,100 Hz A1 peak, quiet late A2 and 0/62 A3/A4 decisions; an
  ungated A2 stays nearly as loud as A1. This tests the timing candidate,
  while the physical latch/data/analog path remains unverified and C2 open.
  A [photo-B5 bit screen](g2/JOINT-MASK04-PHOTO-B5-TONE.md) then checks the
  one DAC data pin suggested by a front-side trace, under the same fixed map.
  The full candidate code peaks at 2,100 Hz for tone and 1,800 Hz for an
  unmodulated carrier in all six bus orders and both latch phases. The
  assumed Y4→74LS273 Q4→DAC08 B5 bit instead peaks at 2,400/2,600 Hz;
  its own level is not an independent line-carrier witness. This does not
  reject the Q4→B5 photo segment, but a higher-weight DAC pin or analog
  node must constrain the output route before C2 can pass.
  The [all-bit carrier-bin audit](g2/JOINT-MASK04-DAC-BIT-CONTRIBUTIONS.md)
  decomposes those same real-PROM samples. At the exact tone and carrier
  bins, the assumed Y7→DAC code-bit-7 contribution equals the entire
  full-code component; all seven lower-bit components are zero in all six
  bus orders and both latch phases. This focuses the next output-route
  experiment on the Y7/latch/DAC MSB path or an analog node. It does not
  prove that the photographed board uses the assumed DAC bus or pass C2.
  The [MSB-only controller-data replay](g2/JOINT-MASK04-DAC-MSB-DATA.md)
  checks two 1,248,256-word mask-`04` PROM runs against the prior trace and
  sample hashes. After the same candidate bandpass, the top bit alone
  gives a 2,100 Hz A1 peak and 0/62 A3/A4 decisions for each call/answer
  selector under both latch phases and six bus orders; lower seven bits
  alone miss 22–23/62. The top-bit route is therefore the most useful
  DAC input to constrain next. The top-bit-only filtered waveform also
  improves the same reference shape fit to R²=0.909/0.900 versus the
  six full-code ranges 0.834–0.838/0.810–0.815. This is conditional on
  the external bandpass and reference. Y7→latch→DAC08 B1/pin 5 and the
  analog line path remain untraced, so C2 remains open.
  The [joint-map free-clock screen](g2/JOINT-MASK04-FREE-CLOCK-MSB.md)
  replays those same two full PROM streams with a periodic sample every
  1,500 microinstructions at each of `127`–`12A`. All four phases give
  a 2,100 Hz A1 peak and 0/62 A3/A4 errors for both full-code and
  MSB-only candidates across the six bus orders and both selectors.
  Distinct byte hashes show that the tone/decision checks do not choose
  the latch phase. A 375-edge PROM divider is not required in this
  conditional fixture; the free-running clock, DAC and analog routes
  remain hypotheses, so C2 stays open.
  The [direct MSB phase replay](g2/JOINT-MASK04-MSB-SEGMENT1-PHASE.md)
  re-executes both 1,248,256-instruction joint-map streams and measures
  phase from the raw candidate DAC top bit, without an analog filter or
  reference decoder. A1 symbol phasors remain steady at 2,100 Hz; all
  31 adjacent A3 pairs reverse by 180° at 1,800 Hz under each of four
  free-clock phases. Their full-byte hashes differ, but their MSB hashes
  agree. This strengthens the conditional segment-1 transmitter evidence;
  Y7→latch→DAC08 B1 and the physical line output remain unverified, so
  C2 stays open and the next test should constrain that route or an analog
  node under labelled photo assumptions.
  The [direct A4 data-phase replay](g2/JOINT-MASK04-MSB-DATA-PHASE.md)
  measures the next 32 raw-MSB phase changes in each executed call/answer
  stream, including the A3→A4 boundary. The frozen D127 four-visit rule
  predicts every nearest quadrant (0/64 wrong distinct steps), whereas
  the opposite phase sign misses six call and eight answer steps. This
  ties the candidate DSC output to the controller's segment-2 dibits
  without the external bandpass or decoder. The sample clock and
  Y7/latch/DAC/line path remain assumptions, so C2 stays open.
  An [executed arithmetic check](g2/JOINT-MASK04-ADC-ROM-WRAPPER-RULE.md)
  now identifies the actual input path in this candidate: `3F8` combines
  the ADC high nibble with R5 into Y, `3F9` reads Am27S31 at `0x100+Y`,
  and `3EB` writes the negative of Q's low nibble to R1. At `3ED`, Y equals
  pre-word R1 on all 6,000 visits and differs on 2,482 visits between the
  paired ADC waveforms. Mask `08`
  keeps R1 fixed and loses the after-fourth-row difference. Use these
  operations to locate an executed decision/output consumer; a table
  lookup and retained state alone do not pass C3.
  A [fixed-phase quadrature screen](g2/RECEIVER-MASK04-QUADRATURE-DECISION.md)
  also finds no exact training fit among 90,000 R1/R12/Q pair choices; the
  training-selected choice misses 25/48 holdout and 39/48 fresh dibits.
  That external I/Q readout is not an executed DSC decision. Continue with
  an instruction-driven multi-sample consumer or a photo-compatible output
  latch/USART route, keeping C3 open and G2 active.
  The [mask-04 `3ED` PROM-latch test](g2/RECEIVER-MASK04-3ED-PROM-LATCH.md)
  finds one all-positive three-bit raw-PROM decode of `3ED`. A hypothetical
  U19 NAND clocks on `3ED→3EA` exactly 24,000 times in each of eleven
  full streams, capturing the R1-derived Y byte after every row. U19 is
  photographed near four-bit latch U12, but the pins and RxD route are
  untraced. No direct or previous-symbol bit among 240,000 choices fits
  training; the selected choice misses 5/48 holdout and 12/48 fresh bits.
  Test a stateful four-row readout or another executed output consumer,
  rather than treating the plausible latch clock as a C3 pass.
  A [differential phase-nibble test](g2/RECEIVER-MASK04-LATCHED-NIBBLE-PHASE.md)
  then treats each captured Y[3:0] as a possible phase index. None of
  240,000 fixed phase/direction/offset/lag choices fits training; the
  training-selected choice misses 16/48 holdout and 10/48 fresh dibits.
  The isolated perfect fresh stream does not generalize. This excludes
  that simple external readout under the fixture, not an executed
  multi-sample receiver; C3 remains open.
  A [paired-row phase-code screen](g2/RECEIVER-MASK04-ROWPAIR-PHASE-CODE.md)
  combines the executed `3ED` Y bytes from rows 0 and 3 of the same ADC
  visit. One fixed eight-state lookup, including the expected 180° carrier
  advance per symbol, gives 0/36 training, 0/48 holdout and 0/48 fresh
  differential-dibit errors with full coverage. Training-exact one- and
  two-sample raw-ADC codebooks cover at most 11/96 independent decisions.
  This is a strong conditional phase-state witness under mask `04`, but its
  lookup/subtraction is external and no USART RxD consumer is identified.
  Test an executed or photo-compatible row-pair consumer and input-level
  variation before passing C3; G2 remains active.
  The [changed-level receive replay](g2/RECEIVER-MASK04-ROWPAIR-LEVEL-CHECK.md)
  tests the frozen eight-state lookup in six more full-PROM runs. At 0.75
  gain, with no clipped PCM samples, it recognizes only 2/24 transitions
  and both decisions are wrong, although the independent reference receiver
  still decodes the waveforms. The lookup is therefore specific to its
  original ADC level. Seek an executed adaptation/decision or a separately
  validated normalized readout; C3 remains open without blocking on wiring.
  The [row-3 gate continuation](g2/RECEIVER-MASK04-ROW3-PARITY-GATE.md)
  finds an input-level-tolerant partial decision: `OR(Y3ED_row3[2:0])`
  XOR its previous-symbol value equals dibit-bit parity on 192/192
  transitions from sixteen full-PROM traces, including six fresh random
  runs. The same gate on raw ADC errs 103/192. A gain-specific full-phase
  lookup recovers 19/24 reduced-gain holdout transitions with five unknown,
  so the second bit and gain adaptation remain open. Identify an executed
  or photo-compatible gate/latch route to USART-01 RxD before passing C3;
  continue with labelled hypotheses rather than waiting for continuity.
  The [phase-47 Boolean continuation](g2/RECEIVER-MASK04-PHASE47-BOOLEAN-DIBITS.md)
  uses row-0/row-3 executed `3ED` Y bytes to form a two-bit phase and
  subtract the previous symbol's phase plus the reference carrier's
  180° advance. The rule was derived on earlier traces, then frozen for
  eight new full-PROM runs at four ADC input levels: **0/96 fresh dibit
  errors**, with complete decisions. This is the first multi-level,
  two-dibit conditional receiver readout. The Boolean circuit and USART
  route are not executed or traced, and carrier-phase tolerance was
  untested in that fixture. Model a photo-compatible latch/consumer and
  actual RxD timing
  before passing C3; G2 remains active.
  The [rotated-carrier replay](g2/RECEIVER-MASK04-CARRIER-PHASE-SCREEN.md)
  qualifies that result: the fixed gate still decodes 90° and 180°
  rotations, but 45° and 135° rotations leave at least 2–5 errors per
  12-dibit stream even after trying all 375 ADC capture visits. The
  reference receiver decodes all of them. Find an executed phase-tracking
  or photo-compatible decision route and retest; this readout alone does
  not pass C3 or block G2.
  The [phase-seed screen](g2/RECEIVER-MASK04-PHASE-SEED-SCREEN.md) then
  varies final-scenario Q and R5 on a 45° carrier trace. Q=`0/10/15`
  never reaches the receive loop; Q=`5` does. Three alternate R5 seeds
  change the captured output but leave at least 6/12 dibit errors after
  all 375 capture visits are considered. Initial Q is an entry choice
  here, not a demonstrated carrier-phase control. Test a dynamic input
  or photo-compatible row latch/output consumer next; C3 stays open.
  The [U12 latch replay](g2/RECEIVER-MASK04-U12-LATCH-REPLAY.md) now
  tests that consumer timing on two complete real-PROM streams. A
  hypothesized row-0-qualified four-bit latch holds Y through two zero
  rows and gives 0/12 nominal dibit errors; clocking it at every raw
  `3ED` edge overwrites the byte and gives 9/12. The qualified latch
  still gives 10/12 errors with a 45° carrier rotation. This constrains
  the proposed clock but establishes neither U12/U24 wiring nor an RxD
  route. Try a phase-tracking input or another four-row consumer, and
  keep C3 open without treating the missing continuity as a blocker.
  The [rotated row-pair codebook](g2/RECEIVER-MASK04-ROTATED-CODEBOOK.md)
  tests whether another fixed lookup could repair that failure. Across
  six real-PROM 45°/135° streams, `(F3,F2)` represents two reference
  phase states even after allowing a constant offset between rotations.
  A 45° table trained on one stream covers both independent streams but
  misses 5/24 dibits. Test a multi-visit or stateful consumer rather than
  treating a new one-visit gate as established; C3 remains open.
  The [two-visit replay](g2/RECEIVER-MASK04-TWO-VISIT-PHASE.md) finds that
  visit 94 separates the observed ambiguous `(F3,F2)` states, but a
  lookup trained on one stream leaves several independent decisions
  unknown. An explicit rule developed on four 45° streams then misses
  2/24 dibits on two new 45° streams and 2/24 on 135° controls. Seek
  retained-state or multi-visit arithmetic with a physical output
  hypothesis; the missing RxD route does not block further experiments.
  The [transient `3F8` bit audit](g2/RECEIVER-MASK04-3F8-TRANSIENT-BIT.md)
  locates the missing information earlier in the executed receive row.
  For 24 ambiguous `(F3,F2)` symbols, the modeled whole Am2901 state is
  identical at visit-47 `3ED`, but `3F8` Y7 and carry separate the two
  reference states 13 cycles after row-0 `3ED` and 11 cycles before row-3
  `3ED`. A frozen external latch/readout makes 0/48 fresh dibit errors
  at 45°/135° with full coverage, while its 0°/90°/180° coverage is poor.
  A four-literal raw-PROM `3F8` decode produces 6,000 candidate latch
  edges at `3F8→3F9` in one full trace plus one startup edge. The edge
  captures exactly the executed Y stream under the timing hypothesis.
  An [explicit one-bit latch replay](g2/RECEIVER-MASK04-3F8-TRANSIENT-BIT.md)
  includes the startup edge and holds Y7 to four later `3ED` observations
  per complete receive visit; all 32 symbol-visit row-3 values agree with
  the executed source. Physical clock integrity remains untested. Test a
  symbol-rate phase-class consumer next; do not promote this conditional bit
  to a traced USART receive decision or block on the missing net.
  The [continuous preamble/data replay](g2/RECEIVER-MASK04-PREAMBLE-SERIAL.md)
  now runs 32 `11` reversal symbols and 16 data symbols without restarting
  the real-PROM receive loop. Two independent streams each give 0/16 data
  errors at 0° with the nominal readout and at 45° with the `3F8`-bit
  readout; all 31 measurable preamble dibits are `11`. Executed symbol
  events are 12,000 microcycles apart, permitting a labelled two-bit
  serial candidate at 6,000 cycles/bit. The oscillator ratio, RxC phase,
  8251A character alignment and DSC-to-RxD connection remain hypotheses.
  Test external SYNDET timing and pin routing next; this progress does not pass C3.
  The [preamble selector and alias audit](g2/RECEIVER-MASK04-PREAMBLE-PHASE-ALIAS.md)
  now tests how to choose between the two external readouts. A row-0 bit
  works at 0°/45° but fails at 90°; a four-value byte lookup fits 0°–135°
  but fails at 180°. In a matched 45°/180° pair, all 32 preamble triples
  of `3ED` row-0/row-3 Y and `3F8` Y at visit 47 are identical, even
  though the data needs different readouts. This excludes any selector
  confined to those fixed-phase preamble bytes under the tested fixture.
  Test another visit or retained phase state before claiming an automatic
  receive decision; C3 remains open and G2 active.
  The [two-visit follow-up](g2/RECEIVER-MASK04-PREAMBLE-TWO-VISIT-SELECTOR.md)
  finds that `3F8` Y7 at ADC visit 94 distinguishes the aliased 45°/180°
  preambles. Combined with row-0 `3ED` Y at visit 47, a frozen external
  selector gives 0/248 preamble and 0/128 data errors with full coverage
  on a new random stream across eight 45° carrier rotations, each a
  576,047-word real-PROM run. A saved 15°–165° challenge yields no fully
  correct case, so the rule does not establish arbitrary phase tracking.
  Test an executed or photo-compatible multi-visit decision and then its
  USART timing; C3 remains open without waiting for net continuity.
  The [cubic transition constraint](g2/RECEIVER-MASK04-CUBIC-TRANSITION.md)
  applies to the separate four-bit two-visit readout. It forces 14 labels
  beyond the 86 observed development keys without fitting held-out answers.
  Four of five unknown decisions on the saved 13-angle real-PROM run become
  correct, leaving 0 errors and one unknown among 611 decisions. Three
  new-seed real-PROM runs at 0°/75°/165° give 0 errors and 0 unknown among
  141 decisions. Key `3C`, physical capture/logic, and RxD/RxC/SYNDET
  remain open; test richer executed state and the serial handoff, not a
  continuity prerequisite. This does not pass C3.
  The [dual-feature consensus](g2/RECEIVER-MASK04-DUAL-FEATURE-CONSENSUS.md)
  uses the other conflict-free four-bit subset as a fallback for the
  cubic rule. A fresh four-angle PROM comparison finds complementary
  unknown cases and no wrong decisions. Re-executing the 13 held-out
  0°–180° streams produces 0/611 wrong or unknown decisions and no
  conflicts between known labels; the alternative covers the remaining
  `3C` case. Both tables, capture clocks and symbol memory remain external
  hypotheses. Test serial timing and the USART receive path next; C3
  remains open until that handoff is supported.
  The [extra-capture-bit screen](g2/RECEIVER-MASK04-EXTRA-CAPTURE-BIT-SCREEN.md)
  reanalyzes eight saved development PROM traces and a separate
  13-angle seed. Adding Y4 or Y5 from either visit as a fifth symbol-state
  bit leaves 122–196 unknown of 611 held-out decisions, versus 84 for
  the four-bit baseline under the same smaller training set. None gives
  a consistent quadratic transition rule across all saved captures.
  This does not reject the dual-feature consensus, which uses more
  development data. The explicit raw-PROM `3F8→3F9` one-bit latch now
  passes its startup and later `3ED` timing check. Test a photo-compatible
  two-visit hold and symbol-rate consumer, rather than adding arbitrary Y bits.
  In two long zero-run PROM handoffs, the candidate Y5–Y7 latch supplies
  the frozen readout at row-3 `3ED` and recovers the controller line bytes.
  A row-0 pre-capture control also recovers them, leaving the physical
  symbol clock phase unresolved.
  The [boundary-impulse replay](g2/RECEIVER-MASK04-CAPTURE-PHASE-BOUNDARY.md)
  shows that one-visit ADC bit-7 flips at 47/94 make only row 3 abstain
  (13/31), whereas flips at 46/93 make only row 0 abstain (11/31).
  Both natural readouts still pass; use photo-compatible clock dividers
  or a natural phase-sensitive fixture to choose the board phase.
  The [sample-clock phase replay](g2/RECEIVER-MASK04-SAMPLE-CLOCK-PHASE.md)
  now verifies the exact 32-cycle receive-visit cadence across 6,000
  executed visits. At an assumed 14.4 MHz microinstruction rate, a
  1,500-cycle sample clock matches the offered 9,600 Hz ADC schedule
  without an edge race only at offsets −3, −2 or −1 from the first
  `3F8→3F9` latch edge. Candidate RxC sampling at sample index 3 has
  1,478–1,480 cycles after visit-94 row 3; index 2 is too early.
  The oscillator divider, counter assignments and physical clock phase
  remain untraced; test those routes and the symbol-rate consumer.
  The [two-visit zero-run handoff](g2/RECEIVER-MASK04-DUAL-ZERO-HANDOFF.md)
  now feeds the controller's actual scrambled eight-zero-octet streams
  through two continuous mask-`04` PROM runs at 75° and 165°. The frozen
  consensus recovers all 63 measurable dibits and eight line bytes in each.
  At 416 modeled 8031 ticks per RxC bit, the narrow external-sync/USART
  handoff consumes all eight bytes without overrun and reaches `AF→B0`
  only for the aligned SYNDET pulse; early, late, absent and opposite
  selector controls remain at `AF`. Capture, serial, sync and ADC paths
  are still assumed, so this is not a C3 pass. Test photo-compatible
  latch/clock/USART routes and naturally timed controller behavior next.
  A [carrier-offset replay](g2/RECEIVER-MASK04-FREQUENCY-OFFSET.md) finds
  0 wrong but three unknown data dibits at +7 Hz with visits 47/94. The
  [adjacent-visit follow-up](g2/RECEIVER-MASK04-OFFSET-VISIT-PHASE.md)
  captures visits 46–48 and 93–95 without refitting either readout.
  Pair 46/93 recovers all 64 +7 Hz data dibits across two seeds, while
  47/94 leaves seven unknown. Two preamble decisions per seed remain
  unknown, and the earlier sample edge is only a working hypothesis.
  The [96-symbol offset stress test](g2/RECEIVER-MASK04-LONG-OFFSET.md)
  now exposes five unknown data dibits across three ±7 Hz cases on a
  fresh seed, with no wrong known decisions; its zero-offset control is
  complete. This rules out claiming complete ±7 Hz recovery from the
  shorter 46/93 fixtures. Capture additional executed visits around the
  unknowns and test a frozen phase consumer, preamble acquisition and a
  photo-compatible latch/USART route before claiming C3.
  The [two-pair long replay](g2/RECEIVER-MASK04-LONG-PAIR-UNION.md)
  combines 46/93 and 47/94 only when their known labels agree. It
  recovers all 380 measurable dibits in the repeated four-case stream,
  but a fresh four-case ±7 Hz seed leaves two data dibits unknown among
  380: both pairs abstain at one symbol and disagree at another.
  The latter 47/94 label is wrong, so an unconditional fallback is unsafe.
  Inspect those executed symbols and freeze a photo-compatible conflict
  or phase signal before another holdout; C3 and physical routing remain
  open.
  The [executed gap audit](g2/RECEIVER-MASK04-HOLDOUT-GAP-AUDIT.md)
  confirms both trace hashes and captures 25 ADC visits around each
  unresolved symbol. A later 94/141 pair recovers the jointly unknown
  symbol but makes seven wrong decisions elsewhere; at the
  preamble-to-data boundary, 46/93 is correct while 47/94 is wrong.
  Do not fit symbol-specific exceptions from those inspected labels.
  Infer a selector from executed state or photo-compatible logic, then
  test it on a new seed and the USART route before claiming C3.
  The [ADC-margin selector](g2/RECEIVER-MASK04-ADC-MARGIN-SELECTOR.md)
  now freezes one such answer-independent signal rule: rank 46/93,
  47/94 and 94/141 by minimum distance from the ADC midpoint across
  the current and previous symbol, taking the first known table result.
  Four fresh 96-symbol ±7 Hz PROM runs yield 0 wrong and 0 unknown
  among 380 measurable dibits, versus two unknown for the conservative
  two-pair control. This establishes a viable conditional readout,
  not physical capture/selector/USART wiring. Constrain those routes
  and challenge intermediate offsets, noise and controller timing;
  C3 remains open.
  The [offset zero-run handoff](g2/RECEIVER-MASK04-MARGIN-ZERO-HANDOFF.md)
  feeds the 8031's actual eight scrambled line octets through four
  ±7 Hz PROM streams. The frozen margin readout recovers all 63
  measurable dibits and exact line bytes in each. At the assumed
  416-tick RxC pace, an aligned external SYNDET pulse alone takes the
  preserved 8031 ROM `AF→B0`; early, late, absent and opposite-selector
  controls stay at `AF`. The candidate ADC and line-side 8251A are
  pictured on separate boards, but the inter-board net, three capture
  clocks and selector remain untraced. This is a conditional handoff,
  not a C3 pass; test those routes and naturally timed CPU events next.
  The [Timer 1 follow-up](g2/RECEIVER-TIMER1-OFFSET-HANDOFF.md) enables
  `TMOD=15 TH1=FC TL1=21 TCON=40 IE=88` in the same paced 8031 probe.
  Both delay cases execute 57 timer interrupts; byte consumption has no
  overrun or emulator error, and only the aligned pulse reaches `B0`.
  A zero-seeded, unheld-RAM15 control drops to state `00`, consumes no
  bytes and overruns seven characters: Timer 1 decrements bank-2
  `R5:R4` at RAM15:RAM14, so zero underflows on its first interrupt.
  A one-time `75:30` seed from four literal ROM reload sites, with no
  per-dispatch gate force, survives the 57 interrupts and again reaches
  `B0` with eight exact bytes; RAM15:RAM14 ends at `74:F7`. This shows
  the forced gate is unnecessary for a plausible inherited countdown,
  but does not establish that `AF` naturally inherits that value.
  The [Timer-paced `AE→AF→B0` replay](g2/RECEIVER-AE-AF-ZERO-HANDOFF.md)
  starts at synthetic `AE` with the ROM's long and short countdown
  literals. The ROM decodes DTE byte `02` into mode `05`, enters `AF`
  after 51 interrupts with RAM15:RAM14=`74:FD`, then reaches `B0`
  with eight exact PROM-derived bytes only for the aligned SYNDET
  pulse. Early, late, absent, opposite-selector and wrong-mode controls
  fail to reach `B0`. Test the predecessor into `AE`, countdown
  inheritance, sync decoder and serial route as labelled candidates.
  Their physical continuity remains open evidence, not a G2 blocker;
  C3 stays open.
  The [one-state-earlier replay](g2/RECEIVER-AD-AE-AF-ZERO-HANDOFF.md)
  begins in synthetic `AD` with only the long countdown seeded. The ROM
  increments `AD→AE` when RAM64 reaches eight, loads the `AE` short timer,
  and reaches `AF→B0` for both aligned real-PROM byte streams after 141
  Timer 1 interrupts. The same timing and selector controls fail. Next
  test the predecessor into `AD` and its countdown inheritance, plus a
  photo-compatible sync/serial route; missing continuity is not a blocker.
  The [sync-hunt alignment screen](g2/RECEIVER-MASK04-SYNC-HUNT-ALIGNMENT.md)
  groups those recovered bits under a **counterfactual internal** `FF` hunt.
  Supplying the first unmeasured `11` dibit and starting hunt at bit zero
  gives seven further `FF` characters followed by four correctly aligned
  data bytes in all four traces. Across eight leading-bit and eight
  hunt-start choices, eight pairs align the data and 56 do not. Repeated
  `FF` fill cannot establish the physical RxC phase or data-byte boundary;
  more importantly, the actual `CC` mode disables internal receive hunt.
  Test a photo-compatible SYNDET/RxD/RxC route and executed USART consumer;
  keep C3 open and G2 active without waiting for net continuity.
  The [conditional controller handoff](g2/RECEIVER-MASK04-CONTROLLER-ZERO-HANDOFF.md)
  extends the real-PROM receive run to eight scrambled zero octets. Both
  scrambler delays at 0° and 45° recover all 32 data dibits; their eight
  line bytes, offered at the preserved 8031 ROM's modeled USART-01 reads,
  descramble to eight zero octets and advance state `AF→B0`, emitting
  `D0 42 81 1A`. Flipping one bit in the last offered byte keeps `AF` and
  its `D0 42 89 9A` frame. This establishes a conditional DSC-to-controller
  behavioral handoff, not a traced RxD/RxC circuit, chip-level 8251A event
  or naturally timed controller entry. Keep C3 open and test candidate
  physical latch/serial routes without treating missing continuity as a
  goal blocker.
  The [external-SYNDET replay](g2/RECEIVER-MASK04-EXTERNAL-SYNC-HANDOFF.md)
  now clocks those saved real-PROM bits through a narrow 8251A external-sync
  shift/RxRDY model before offering assembled bytes to the same executed
  8031 AF detector. A pulse before the first data RxC edge yields eight
  exact line bytes and `AF→B0` in four fixtures; pulses one bit early,
  one bit late or one byte early leave `AF`, and no pulse yields no RxRDY.
  This constrains a proposed sync gate, but its source, timing and physical
  routes are assumptions. C3 remains open.
  A [paced continuous-controller replay](g2/RECEIVER-TIMED-CONTROLLER-HANDOFF.md)
  clocks the same saved real-PROM bits through a narrow external-sync/RxRDY
  model at 416 assumed 8031 machine ticks per bit while the unchanged 8031
  ROM runs its main loop. With the matching DTE selector (`40` for delay 5,
  `60` for delay 18), all four aligned fixtures deliver eight bytes without
  overrun and reach `AF→B0`; early, late, absent-pulse and opposite-selector
  controls remain at `AF`. This removes the immediate-read shortcut but not
  the assumed SYNDET source, RxD/RxC wiring or synthetic controller inputs.
  Keep C3 open.
  The [first-non-`11` SYNDET screen](g2/RECEIVER-SYNDET-PREAMBLE-TRANSITION.md)
  rejects a data-dependent shortcut: under either modeled controller
  scrambler delay, 64 of 256 possible first payload octets retain an
  initial `11` dibit after the true data boundary. Pulsing on the first
  non-`11` dibit then shifts the paced USART byte in representative
  fixtures. The [A3→A4 frame edge](g2/CONTROLLER-SYNDET-EDGE-TIMING.md)
  precedes a *local transmit* write, not an observed remote bit. Seek a
  payload-independent receive boundary event or photo-compatible sync
  route before treating aligned SYNDET as explained; C3 stays open.
  The [nonzero frame-mode handoff](g2/RECEIVER-MASK04-NONZERO-FRAME-HANDOFF.md)
  carries four representative late-trigger payloads through the real PROM
  and paced controller, including two cases whose first data line octet is
  a full `FF` preamble-like byte. All four 768,047-word runs
  recover 63/63 measurable dibits, eight line octets and the exact nonzero
  first payload; data-dependent bit-66 or bit-72 SYNDET pulses change
  USART byte alignment. This extends the conditional C3
  result but does not identify the physical sync source or serial route.
  The [line-USART write screen](g2/RECEIVER-USART-REINIT-SCREEN.md)
  instruments the Timer-1-paced `AD→AE→AF` controller path and finds no
  port-`05` control write before or during eight received bytes, in
  either scrambler direction or absent-pulse control. Its only control
  writes are five bytes to DTE-side port `06`. Thus a late 8031 reset
  of the line-side 8251 does not supply the required byte boundary in
  this executed fixture; test external SYNDET or receive-clock gating,
  while keeping earlier startup behavior as a separate possibility.
  The [held-SYNDET/RxC-gate screen](g2/RECEIVER-RXC-GATE-SCREEN.md)
  tests six saved real-PROM streams through a narrow 8251/8031 model.
  A SYNDET high established before data plus RxC first enabled at bit
  64 gives exactly the earlier aligned-pulse result; gates at bit 0,
  63, 65 or never fail the complete-byte check. This supplies a second
  conditional sync architecture, not a traced gate or receive-boundary
  signal. Keep C3 open and test a photo-compatible gate driver.
  The [four-bit phase readout](g2/RECEIVER-MASK04-FOUR-BIT-PHASE.md)
  combines row-0 `3ED` Y bits 0/1/3 with transient `3F8` Y7 in one
  frozen seven-entry table. Two new continuous preamble/data streams at
  each of 0°/45°/90°/135°/180° yield 0 errors and 0 unknowns across
  470 differential dibits without a per-angle selector. A third stream
  at eight intermediate angles yields 27 wrong and 152 unknown decisions
  of 376; within the data portion, 27/128 are wrong and 67/128 unknown.
  The collision audit finds same-code conflicting phase states at four
  angles and already-known-code mismatches at all eight, so adding the
  two unseen table entries cannot make this four-bit memoryless readout
  phase tolerant. Test a second visit or other retained state and then
  repeat the controller handoff. Keep C3 open; the latch and RxD route
  remain explicit photo-compatible hypotheses, not a reason to block G2.
  The [two-visit transition audit](g2/RECEIVER-MASK04-TWO-VISIT-TRANSITIONS.md)
  captures executed `3F8` Y at symbol visits 47 and 94 on the same eight
  intermediate-angle traces. Three selected bits give a compact phase rule
  that recovers all 376 development dibits, but a new stream exposes 9/16
  data errors at 45° and 5/16 at 135°. Using Y6/Y7 from both visits as a
  four-bit symbol state makes all 987 inspected dibit transitions
  non-conflicting. Its frozen 86-entry table has 0 wrong and 5 unknown
  decisions of 611 on a further fresh stream across 13 angles. This
  localizes useful information in executed arithmetic, but the table is
  external and the five unseen transitions are unresolved. Seek an
  executed or small photo-compatible consumer before repeating the USART
  handoff; C3 remains open and G2 active without a continuity prerequisite.
  The [fixed-phase-state audit](g2/RECEIVER-MASK04-PHASE-STATE-AUDIT.md)
  excludes a 16-entry absolute-phase table plus constant advance: 696
  same-state `11` reversals force a two-quadrant advance, while observed
  transitions `0→4→8→0` require a nonzero net state-phase change. A
  direct transition decision or extra retained/timing state remains
  testable; this negative result does not block C3.
  A [direct two-output Boolean screen](g2/RECEIVER-MASK04-TRANSITION-PLA.md)
  fits all 86 known transition keys with 17 product terms, but makes
  20/987 leave-angle-out errors and 2/611 fresh-stream errors, both on
  previously unseen data keys. This rejects that frozen circuit as a
  complete receive readout; test additional executed features or retained
  state before a serial/USART handoff.
  A [mask-04 TEST-source audit](g2/RECEIVER-MASK04-FLAG-CONDITION.md) checks
  all 16 zero/sign/carry/overflow, current/previous and polarity choices.
  Only inverted previous sign, carry and overflow sustain all four rows
  under held `09`; each retains 1,312/1,500 after-fourth-row differences
  for paired waveforms. None changes TEST at any executed conditional
  command. The 234–282 changed `3EA` TEST levels occur on PLP, which
  ignores TEST. This narrows the flag substitution route without making
  unknown TEST wiring a blocker; pursue an output consumer or a different
  input/field hypothesis for C3.
  The [same-map four-row echo replay](g2/JOINT-MASK04-FOUR-ROW-ECHO.md)
  uses the **exact** mask-`04` controller-driven transmit samples as a
  delayed, half-scale ADC echo, with zero, independent remote and mixed
  controls. Both call and answer complete the 128-sample fixture; five
  remote-responsive bytes include Y3F8/Y3F9/Q/R1/R12, but none halves
  its mixed-input echo response from the first to last 32-sample window.
  This excludes rapid direct-byte attenuation in that fixed fixture,
  not mode-controlled echo cancellation. C4 still needs a justified
  train/freeze route and output residual.
  The [controller-frame D3EB mode test](g2/RECEIVER-MASK04-FRAME-MODE-3EB.md)
  offers the observed A3→A4 third-byte `81→A1` edge to mask-`04`'s
  untraced wrapper D input. Both held bytes sustain all four receive
  rows. The edge changes R0/R1/R10/R12/R13 and Q, but each completed
  post-edge state immediately matches the target held-byte control;
  the reverse edge mirrors it. Conditional TEST/PC and ADC-sensitivity
  counts remain unchanged. That active direct-byte route does not show
  training memory or freeze under this fixture. Try another mode lane
  or output path for C4; do not treat the missing wire as a blocker.
  The [frame-byte receive-decision replay](g2/RECEIVER-MASK04-FRAME-MODE-DECISIONS.md)
  uses the same direct `3EB` hypothesis in eight 192,047-word PROM runs.
  Held `01`, `81`, `A1` and a boundary `81→A1` edge change the full trace
  but leave all selected Y5–Y7 captures and 15/15 frozen receive decisions
  identical at both 75° and 165°. The direct frame route is compatible
  with this conditional C3 readout, but remains untraced and supplies no
  C4 train/freeze evidence. Test a longer mode-qualified handoff and a
  different residual/output route.
  The [long frame-mode zero-run handoff](g2/RECEIVER-MASK04-FRAME-MODE-ZERO-HANDOFF.md)
  executes two 768,047-word receive traces with the hypothetical `81→A1`
  wrapper input at the preamble/data boundary. Both recover all 63
  measurable dibits and the controller's eight scrambled line bytes;
  aligned SYNDET alone moves the paced controller `AF→B0`. Full PROM
  digests differ from the held-`01` baseline, so the mode route is active
  under this fixture. Physical mode/serial/sync nets remain untraced;
  this is conditional C3 behavior, not C4 freeze evidence.
  The [same-map receive decision screens](g2/JOINT-UPPER-RECEIVE-DECISION.md)
  then run seven periodic/nonperiodic reference streams for 24,000 ADC
  visits each. No direct Y/Q/RAM bit at any of 1,500 fixed symbol phases,
  nor any one-byte codebook of at most 16 values using current, XOR or
  symbol-difference state, fits even the 36-dibit training set exactly.
  Seek a microinstruction-motivated multi-sample or separately latched
  decision; input-sensitive ROM addresses alone do not pass C3.
  A [single-ADC-pulse replay](g2/JOINT-UPPER-ADC-PULSE-MEMORY.md) supplies
  a timing clue on the same map. One `59` byte among otherwise identical
  `09` bytes changes Q, RAM 10–13 and subsequent `3F9` ROM addresses through
  visit 5,999 when placed at visit phase 0, 1 or 4 modulo five. At phase 2
  the effect ends immediately, and at phase 3 it lasts two further visits.
  The phase classes repeat 90 visits later. This is retained modeled state,
  not a decoded bit; use the five-visit cadence to constrain the next
  multi-sample receive/output-latch test.
  The [five-phase sampled-state DPSK screen](g2/JOINT-UPPER-SAMPLED-STATE-DPSK.md)
  uses an external known-carrier decoder on reached Y/Q/RAM bytes at ADC
  sample phases. Center-sampled `Y3F8` yields 0/36 training but 7/48
  holdout errors, then 13/48 errors on four fresh random streams; the
  direct ADC input gives 0/48. It preserves a distorted waveform rather
  than a decoded DSC bit. Test paired echo/remote inputs or a distinct
  receive output latch before assigning this subtraction to C3 or C4.
  The [paired own-echo feed](g2/JOINT-UPPER-ECHO-FEED.md) uses the verified
  candidate A4 transmit-code sequence as a delayed, half-scale ADC echo,
  with zero and independent-remote controls. In both call and answer
  fixtures, `Y3F8` output change stays near the injected echo level across
  four 32-sample windows; it does not show a falling residual. This short,
  fixed receive fixture has no identified echo-train/freeze control and
  cannot pass or exclude C4. Seek a mode-qualified path and output site,
  while testing C3 independently.
  The [interrupt-paced A3→A4 frame-edge check](g2/CONTROLLER-A3-A4-MODE-EDGE.md)
  finds no held CD4094-frame or P1 bit that separates all A3 from A4
  iterations. The exact third-byte `81→A1` edge occurs once at A4 entry in
  each call/answer run, but bit 5 also rises earlier and the frame `D0 42 A1 BA`
  is held in A3. Test a history-qualified edge decoder only as an explicit
  mode-input hypothesis, with a no-edge control; do not identify that boundary
  as echo freeze or infer a physical DSC wire from it. C3/C4 remain open, not
  blocked by the missing mode-route trace.
  The [all-state-byte echo screen](g2/JOINT-UPPER-ECHO-OUTPUT-SCREEN.md)
  extends the same paired controls to Y at `3F8–3FA`, Q and all 16 RAM bytes.
  Eight bytes respond to remote input in both selectors, but none halves its
  mixed-input echo response from the first to last 32-sample window. Lower
  echo response at Y3FA/Q/R10/R13 accompanies lower remote response. This
  narrows direct-byte residual sites under the fixed 128-sample fixture;
  next test a justified mode-controlled or separately latched receive route,
  and keep C3/C4 open without waiting for a physical continuity trace.
  The [joint-map echo washout](g2/JOINT-UPPER-ECHO-WASHOUT.md) runs
  128 own-transmit-echo samples followed by 64 identical zero samples
  in four 288,047-word real-PROM traces. The late training state is
  input-dependent, but all modeled Q/RAM and Y bytes match the zero
  control by the third tail ADC visit, and the complete final states
  agree. A longer fixed-mode run at those internal sites is unlikely
  to expose echo taps; model the photographed external MCM93422 memory
  or a train-enable route next. This does not close C4.
  The [external-RAM bus screen](g2/JOINT-UPPER-RAM-BUS-SCREEN.md) runs
  2,048 steady receive visits under constant and varying ADC bytes.
  None of the eight reached Y sites supplies a simple incrementing
  8-bit RAM address, and no bare PROM bit is low only once per loop.
  U18 D2/D4 pulse high at `3EC` and D7 at `3EA`; the DSC 3557 photo
  shows a 74LS163 counter and 74LS157 mux beside four 256×4 RAMs.
  Test a labelled external counter/mux, write-strobe and return-bus
  hypothesis instead of assuming the present internal-Q/RAM fixture
  already models the echo-tap store. Keep C4 open.
  A [computed-call source screen](g2/RECEIVER-DISPATCH-SOURCE.md) now exposes
  another fixture dependency: the long `D3F8` receive loop uses a constant
  scenario index of 2 at `3EC`. Under the same map and seed, modeled Y or
  previous-Y indices never visit `D3F8`, while a Q-derived index visits it
  1,001 times for held `09` but only once for held `59`. On two complete
  reference ADC streams, Q-derived dispatch also exits after one visit,
  versus 24,000 visits under constant index 2. Before treating the
  loop as a continuous receiver, constrain the `3EC` B-input source and
  rerun nonperiodic samples under a surviving dispatch schedule. Keep the
  constant-index results as conditional algorithm probes, not a physical
  receiver or echo-canceller demonstration.
  A [two-row dispatch follow-up](g2/RECEIVER-DISPATCH-SOURCE.md#a-two-row-index-schedule-survives)
  finds that alternating `3EF` and `3F7` survives both 128-sample reference
  streams with 12,000 ADC visits. In paired
  32-sample detail, all 3,000 ADC bytes are selected and 2,781 of 3,000
  following Am27S31 addresses differ between waveforms on the same PC path.
  Test a generalizing receive decision on this interleaved schedule, then
  constrain its counter/buffer index and output routes; the two-row sequence
  is still an explicit hypothesis, not recovered board wiring or a C3 pass.
  A later [four-row condition screen](g2/RECEIVER-FOUR-ROW-CONDITION.md)
  corrects the earlier restriction: a full `0→1→2→3` cycle also sustains
  both reference ADC streams under five assumed TEST sources/polarities.
  Under the then-selected mask `08`, its fourth row erases the tested
  RAM/Q input difference. A
  [third-row latch screen](g2/RECEIVER-FOUR-ROW-LATCH-SCREEN.md) finds no
  fixed-phase direct Y/flag bit that generalizes as a received dibit;
  C3 remains open.
  A [byte-wide sampled-state screen](g2/RECEIVER-FOUR-ROW-SAMPLED-STATE-DPSK.md)
  tests Y, Q and four RAM bytes as candidate received samples on that full
  path. Twenty of 1,200 external-decoder readouts fit the training dibits,
  but none also fits holdout. The best has 7/48 holdout and 12/48 fresh
  validation errors. This narrows simple output-latch hypotheses; it is
  not an executed DSC decision or a USART RxD result.
  A [timed caller handoff](g2/RECEIVER-FOUR-ROW-CALLER-HANDOFF.md) releases
  the executed `3EA` wrapper after 1,500 ADC visits. Releasing `3ED` just
  after the ADC-sensitive third row carries five distinct RAM/Q states into
  the caller and leaves three distinct terminal states across five input
  patterns. Releasing it after the fourth row collapses all five to one.
  The sole changed later TEST is at nonbranching `1AA`; all PC paths match.
  This points to a pre-fourth-row latch or different mode timing to test,
  rather than an executed receive bit on the current route.
  A [raw-PROM latch-gate screen](g2/RECEIVER-PROM-ROW-LATCH-GATE.md) now
  finds two minimal three-literal decodes that isolate `3FA` on the reached
  path. A three-input NAND would rise on `3FA→3ED`; both decodes yield exactly
  1,500 such edges and capture input-sensitive `3FA` Y bytes in each of five
  full real-PROM traces. The board contains a compatible SN74LS10N, but its
  pin route, latch setup phase and USART consumer remain hypotheses. Use
  this timing lead for an executed output-route test; C3 is still open.
  An [all-phase latch-byte screen](g2/RECEIVER-PROM-LATCH-SAMPLE-PHASE.md)
  then tests the captured `3FA` Y stream at every 47/46-visit ADC-sample
  phase. None of 470 fixed external differential readouts fits the 36
  training dibits; the best misses 38/48 holdout and 37/48 fresh decisions.
  The exact PROM edge therefore does not make this Y-only route a usable
  PCM/USART source. Try a different latch data source or an executed
  stateful decision while keeping C3 open.
  The [raw-PROM ADC enable-phase screen](g2/RECEIVER-PROM-ADC-ENABLE-PHASE.md)
  finds a concrete buffer-gate hypothesis for that same path. A one-cycle
  latched `!U10.D1 & U10.D3 & U10.D7` level enables only `3F8` on all
  3,000 reached ADC visits; its same-phase level instead coincides with
  `3F7`'s ROM read. The ADC-fed replay has the same full-state trace digest
  as the PC-qualified baseline. A shorter two-literal gate also enables
  high-slice D at `3FA` and exits after 95 ADC visits. This constrains OE
  timing under the joint map, but the U10-to-74LS244 wire, dispatch index,
  receive decision and USART output remain unverified; C3 stays open.
  The [two-row receive-decision screens](g2/RECEIVER-TWO-ROW-DECISION.md)
  now run seven independent streams through that same schedule. No direct
  Y/Q/RAM bit, previous-symbol byte difference, small byte codebook or ALU
  flag fits the 36-bit training set exactly at any of 750 fixed phases;
  the nearest state-bit fit has 27/48 holdout errors. Seek an
  instruction-motivated multi-sample decision or separately clocked output
  site, and require a generalizing bit plus a candidate USART RxD route
  before calling C3 passed.
  A [two-row ADC pulse replay](g2/RECEIVER-TWO-ROW-PULSE-MEMORY.md) now
  shows why a single-site readout can miss useful state: one changed high
  nibble on the interleaved path leaves one of four late Q/ROM-address
  offset classes. Eleven of fifteen tested high-nibble values retain a
  difference through 3,000 ADC visits, including two sample-length holds;
  the other four reconverge within two visits. The controller input,
  dispatch index and output route remain hypotheses. Use this quantized
  state response to design a multi-sample receive decision and validate it
  on independent symbol streams; do not equate a persistent offset with a
  recovered dibit or echo cancellation.

  Mappings that cannot express the transmitter's minimum operations are
  dropped. *This is the key change:* fields get scored by algorithmic meaning
  rather than statistical plausibility.
- **A5 Cycle budget.** For microcycle = 14.4 MHz / k (k = 1…4), compute the
  microinstructions available per 9600 Hz sample and per baud. Compare these
  with loop lengths in the listing. The main loop must close in a whole
  number of samples.
  The [joined cycle-divisor screen](g2/PHOTO-TX-CYCLE-DIVISOR.md) executes
  `k=1…4` with the real PROMs and a counter-qualified sample clock. The
  four-word loop gives `375/k` edges per 9,600 Hz sample; 832 samples are
  captured in every case. Under the same D127 pulse and analog hypotheses,
  only `k=1` has the 2,100 Hz A1 peak and zero filtered A3/A4 dibit errors.
  This constrains that fixture, not the untraced physical divider or C2.

### Phase B: optional physical checks to discriminate candidates

The [assumption and blocker rules in PLAN.md](PLAN.md#uncertainty-is-a-reason-to-experiment-not-a-goal-blocker)
apply throughout G2. Start with photo-based candidate connections and run
Phases A and C under explicit alternatives where a net is ambiguous. The
checks below can confirm or reject candidates if they become available; none
is a prerequisite or a reason to stop executable experiments.

Listed in order of value per effort:

- **B1 Trace USART 01/05 pins** (TxD, RxD, TxC, RxC, SYNDET, RTS/CTS) and the
  mode-0 shift-chain outputs to their destination board/connector pins. This
  settles E2 and A2.
- **B2 About 25 unpowered continuity checks on DSC2847:**
  - 8X02 AC0–2 and TEST;
  - the latches at positions 5/6/29/30 → Am2901 I0–I8, A0–3, B0–3, Cn, D-bus
    source;
  - ADC0800 data outputs, output enable, end-of-conversion and clock on DED
    3558 to their buffers and DSC 2847 input path; trace the photographed
    DAC08HP input bits, adjacent 74LS273/74LS373 data and control routes,
    and current-output route;
  - the 14.4 MHz divider (positions 25/20/21/14) → 8X02 CLK.

  This collapses the mapping alternatives.
- **B3 Dump the remaining programmable devices** on DSC 3557 (810111, 810112)
  and confirm 810241 = the Am27S31. Possible quarter-square multiply tables
  or RAM address sequencers would change the picture.
- **B4 If the modem can be powered:**
  - (a) record the line output with a sound card in analog loopback/test mode
    (expect energy at 1200–2400 Hz centred at 1800 Hz, 1200 baud, and a
    2100 Hz tone at answer);
  - (b) logic-analyser capture of 8X02 A0–A9 and the clock. A real
    microprogram address trace ends the mapping question outright.

### Phase C: confirm "how" by co-simulation

- **C1 Reference model.** Write a compact Python V.26 ter modem in 8-bit
  fixed point: DPSK Tx with RC shaping at 9600 Hz, Rx demodulation, and LMS
  echo canceller. Use it only to generate expected signatures (table index
  sequences, line-output sample spectra, bit decisions), not as a bit-exact target.
- **C2 Transmit test.** Drive the surviving mapping(s) with the real
  controller's command frame for "data 2400" plus the synchronous scrambled
  bitstream from USART 01. Capture the byte at the photographed DAC08HP's
  B1–B8 inputs through explicit 74LS273 and, if used, 74LS373 clock/data
  hypotheses; only a traced or independently constrained route may be called
  the line-output
  stream. Pass criteria:
  - the identified line-output sample stream has its spectral peak at 1800 Hz
    × (true sample rate / 9600);
  - the phase steps follow the dibits;
  - "segment 1" yields 180° reversals;
  - the 2100 Hz state yields a tone.
  The [PC129 ROM-bank ablation](g2/JOINT-MASK04-TX-ROM-BANK-ABLATION.md)
  holds the full controller-fed fixture fixed and switches just the
  Am27S31 `129` A8 bank. Both call and answer runs have changed full
  trace digests but identical 832-byte candidate Y samples at `129` and
  the same tone/data scores. A separate `12E` bank switch is a null control: that
  address has zero visits in the sustained `127–12A` loop. Therefore
  upper-bank `129` selection is not established as the source of this
  candidate waveform. Inspect where a changed `129` operand first reaches
  retained state before attributing carrier generation to that ROM region;
  C2 remains open pending a constrained DAC/line route.
  The [short differential trace](g2/JOINT-MASK04-TX-ROM-IMPACT.md)
  establishes why: all 1,014 selected `129` ROM values change in a
  4,096-cycle tone-window test, changing ALU `f` and temporary writes,
  while Y7 and the program path do not. Transient `12A` Y lower bits do
  change, so the operand is active internally; the tested candidate
  MSB output is simply insensitive to this bank choice.
  The [full controller-fed phase screen](g2/JOINT-MASK04-TX-BANK-PHASE.md)
  checks the adjacent `12A` Y site on both selectors. Changing `129` A8
  changes only `12A` Y0 on 75,012/75,018 loop visits; all 375 divided
  clock phases see at least one changed sample. Phase 0 captures 198/202
  changed bytes out of 832, each worth 16 DAC counts on the six surviving
  bus orders, yet both banks retain a 2,100 Hz tone and 0/62 A3/A4
  filtered data errors. This is a specific ROM-sensitive output candidate,
  still conditional on the latch, DAC and analog route.
  The [raw-edge timing check](g2/JOINT-MASK04-TX-BANK-EDGE-TIMING.md)
  finds that a pre-edge capture at U10 D2 rise (`129`) or fall (`12A`)
  misses the bank-dependent byte; only settled `12A` Y differs on
  221/1,014 falling-edge visits in the held-tone run. Constrain a
  post-`12A` capture phase before promoting this candidate to C2 evidence.
  The [R1/Y7 phase replay](g2/JOINT-MASK04-TX-PHASE-ACCUMULATOR.md)
  then verifies the executed mechanism over the first 18 continuous
  controller-derived A4 dibits of both selectors: R1 advances by D127
  modulo 256 on every visit, Y7 equals R1 bit 7 at all four loop words,
  and four-visit pulses create the exact expected quadrants. This
  explains the candidate 1,800/2,100 Hz digital output under the
  assumed 9,600 Hz latch clock, while C2 still requires a constrained
  DAC and analog line route.
  A [photo-B5 alternative](g2/JOINT-MASK04-PHOTO-B5-Y7-ROUTE.md)
  takes the exact saved Y7 samples through an assumed Y7→LS273 D4
  input and the visible-candidate Q4→DAC08 B5 segment. The B5-only
  eight-count output retains the tone, reversals and 0/62 filtered
  A3/A4 decisions for both selectors under the external A2 gate/filter.
  This is a scaled version of the existing Y7 waveform, not a second
  independent transmit witness or a physical C2 pass. The alternative
  B5 and B1 bus assignments need a distinguishing pin/output constraint.
  The [controller-duration hold replay](g2/JOINT-MASK04-A2-LE-TIMED.md#photo-suggested-b5-path-under-the-same-controller-hold)
  extends the photo-suggested B5 route to both uninterrupted
  2,040,256-word selector runs. All 24 B5/B5+B6 timing cases retain a
  2,100 Hz tone, modeled A2 silence and 0/62 A3/A4 filtered errors;
  Y7 samples agree across the two tested raw-PROM latch phases. This
  constrains a longer candidate timing path, while Y7→D4, the A2 hold
  gate and the analog line route remain assumed, so C2 is still open.
- **C3 Receive test.** Encode reference line samples as ADC0800 complementary
  bytes under an explicit reference range and conversion schedule, feed them
  through the identified input path, and check that recovered bits reach the
  USART-01 receive side.
  The [matched-tail U12 replay](g2/JOINT-MASK04-CARRYOVER-LATCH-PULSE.md)
  establishes a conditional previous/current sample pair at an executed
  raw-PROM gate: the qualified latch holds the previous nibble at row 3
  after internal DSC state rejoins. The existing fixed Boolean consumer
  fails at 45° carrier phase, and the U12/USART wiring is untraced.
  The [U12 collision](g2/JOINT-MASK04-U12-CODE-COLLISION.md) shows that
  its assumed row-pair stream loses a controlled `1F`/`6F` sample
  distinction. The [history scan](g2/JOINT-MASK04-RECEIVE-HISTORY-SCAN.md)
  finds only R12/R13 carryover for two words after the next ADC selection
  in five legal waveforms. Test a preselection latch or a changed
  mode/feedback path on fresh legal symbol transitions and then seek a
  causal bit route to USART-01; do not promote the U12-only Boolean rule.
- **C4 Echo canceller.** Feed the board's own transmit signal back as echo
  and check that the residual falls while training is enabled and freezes
  when it is commanded off. The
  [sample-paced high-nibble return test](g2/JOINT-MASK04-RAM-HIGH-RETURN-EXIT.md)
  exits the receive loop under the previous-overflow TEST assumption,
  while its write-only and read-only controls sustain it. A
  [previous-carry TEST choice](g2/JOINT-MASK04-RAM-CONDITION-RESCUE.md)
  sustains the same high return, but the
  [own/remote/mixed challenge](g2/JOINT-MASK04-RAM-CARRY-ECHO-SCREEN.md)
  increases rather than attenuates the late `3FA` own-echo code proxy.
  Its [arithmetic audit](g2/JOINT-MASK04-RAM-CARRY-ARITHMETIC.md)
  finds R10 fixed at `10` at every tested `3FA` operand read, so that
  output's high nibble is the delayed return high nibble plus two.
  The [paired propagation trace](g2/JOINT-MASK04-RAM-CARRY-PROPAGATION.md)
  finds that changed R13 lasts six cycles and rejoins at `3FC` on both
  legal streams, with no changed downstream ALU, Q, TEST or PC path.
  Test a photo-compatible `3FA` output latch and line consequence, or a
  signed/mode-qualified return that reaches a later consumed operand.
  The [sample-paced latch screen](g2/JOINT-MASK04-RAM-CARRY-LATCH-PHASE.md)
  finds `3FA` Y constant within every held ADC sample on all eight controls;
  all 46 fixed phases preserve the larger late echo code contrast.
  A phase choice at this output site therefore does not rescue this route.
  An [alternative `3FC` return](g2/JOINT-MASK04-RAM-CARRY-3FC-PROPAGATION.md)
  changes the following `3FD` ROM calculation on both legal streams while
  sustaining the loop. Test that new output site on the four echo controls;
  the changed state still rejoins and does not yet prove cancellation.
  The [four-input `3FD` replay](g2/JOINT-MASK04-RAM-CARRY-3FD-ECHO-SCREEN.md)
  finds input-sensitive delayed codes, but their own-echo and
  mixed-versus-remote contrasts both rise from early to late training at
  every fixed sample latch phase. The frozen effect lasts only the first
  three zero-tail samples under this three-sample RAM lag.
  The [word-level arithmetic audit](g2/JOINT-MASK04-RAM-CARRY-3FC-ARITHMETIC.md)
  checks 48,000 reached `3FC`/`3FD` words and finds fixed R10=`10`
  and R5=`00` at the two consumed operands. The route is a delayed
  RAM-code-to-ROM lookup, without a varying trained coefficient at
  these sites under the tested mode.
  No tested RAM output is yet a measured or selectively falling echo residual.

## 3. Acceptance for G2

"What it is for" counts as answered at ≥80% when **A1 + A2 + E2** are
consistent with one standard and either **A4 or B4(a)** shows a transmit
modulator in the microcode or on the line.

"How it works" counts as answered when **C2 passes** for one mapping and
**C3 or C4** passes, with routine names in
[PROGRAM-READING](assumed/PROGRAM-READING.md) rewritten from arithmetic
descriptions to modem functions.

## 4. Deprioritised

- Further handler-by-handler contracts and coverage percentages under
  unconstrained mappings.
- Extending the arbitrary `c,p,l,h` bridge.

Existing results stay reproducible and are reused as tooling: the executor,
the reset witnesses and the 8031 harness.
