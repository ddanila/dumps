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
  - Interpret 30–7F as parameter blocks, e.g. phase increments: 48 = 1800 Hz
    and 56 = 2100 Hz per 256-step phase at 9600 Hz; byte 0x34 = 0x30.
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

  Mappings that cannot express the transmitter's minimum operations are
  dropped. *This is the key change:* fields get scored by algorithmic meaning
  rather than statistical plausibility.
- **A5 Cycle budget.** For microcycle = 14.4 MHz / k (k = 1…4), compute the
  microinstructions available per 9600 Hz sample and per baud. Compare these
  with loop lengths in the listing. The main loop must close in a whole
  number of samples.

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
- **C3 Receive test.** Encode reference line samples as ADC0800 complementary
  bytes under an explicit reference range and conversion schedule, feed them
  through the identified input path, and check that recovered bits reach the
  USART-01 receive side.
- **C4 Echo canceller.** Feed the board's own transmit signal back as echo
  and check that the residual falls while training is enabled and freezes
  when it is commanded off.

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
