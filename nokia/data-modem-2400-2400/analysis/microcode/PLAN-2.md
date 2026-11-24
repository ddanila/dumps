# Plan 2: establish what the Am2901 microprogram does, and why

**Question to answer (target ≥80% confidence):** what signal-processing job
the DSC2847 bit-slice board performs in this modem, and how the 1024-word
microprogram implements it.

[PLAN.md](PLAN.md) was accepted: the microcode now runs under six candidate
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
| E1 | The 8031 scrambler pair (d = 18 or 5, length 23, selectable per direction) is exactly V.26 ter §5: GPC = 1+x⁻¹⁸+x⁻²³ (call), GPA = 1+x⁻⁵+x⁻²³ (answer). V.26 defines no scrambler, V.26 bis has none and V.22/V.22 bis use 1+x⁻¹⁴+x⁻¹⁷. V.32 uses the same pair, but it runs at 4800–9600 bit/s. | [CONTROLLER-SCRAMBLER](assumed/CONTROLLER-SCRAMBLER.md), ITU-T V.26 ter (11/88) §5, §6.1 | High |
| E2 | Under Intel 8251A semantics, the USART at 01/05 is programmed `CC` + sync char `FF` + `15`. That is synchronous mode with 8-bit characters, external sync detect, and Tx/Rx/error reset enabled. Scrambled bytes are written to 01 and descrambler input is read from 01. **USART 01/05 is therefore the synchronous line-side bitstream to and from the modem DSP.** USART 02/06 takes `6E`/`7E`/`6A`/`66` (async ×16, chosen by switches) or `EC` (sync), so it is the DTE port. V.26 ter specifies exactly these DTE modes: synchronous or start-stop. | [CONTROLLER-PROGRAM](assumed/CONTROLLER-PROGRAM.md), 8251A data sheet | High (semantics); the physical net still needs tracing |
| E3 | Timer 1 reloads FC21. With the 11.9808 MHz oscillator on DSU 3556, that gives a **1.000 ms tick**. The state machine at 1000–15xx (state in RAM34, countdown in bank-2 R7:R6) loads 1805, 2605, 250, 2000, 455, 60, 70 … ms. These match the V.25/V.26 ter operating-sequence windows: ≥1.8 s silence (2.15 ± 0.35), ≥2.6 s 2100 Hz tone (3.3 ± 0.7), 250 ms silences, the 2 s rate-pattern timeout and a 500 ± 50 ms echo-suppressor-disable tone. | `controller-linear.asm` 11B6–11E3 etc., V.26 ter §6.3 | Medium-high (state-by-state mapping not yet done) |
| E4 | The boards are date-coded 8406/8410 and their ICs 1983. V.26 ter was approved in 1984. The front panel reads "2400/2400" (duplex), unlike Nokia's DS2839 "2400/1200" (V.26 bis-like). | Photographs, collector listings | Medium |
| E5 | The DSC2847 has its own **14.400 MHz** oscillator (CK1144AC). 14.4 MHz = 1500 × 9600 = 12000 × 1200 baud = 8000 × 1800 Hz. | Whole-board photo, `board/inventory.json` | Fact; the microcycle divisor is unknown |
| E6 | Am27S31 bytes 00–13 are a 16-point sine plus 4 wrap entries, which allows sin(i) and cos(i) = table[i+4] without wrapping, i.e. quadrature. 1800/9600 = **3/16**: at a hypothetical 9600 Hz sample rate (8 samples/baud), the 1800 Hz carrier advances exactly 3 entries per sample. 100–140 is a 65-entry quarter sine, i.e. a fine 256-step phase, as needed for carrier tracking (V.26 ter requires ±7 Hz). 68–6F `00 01 02 03 01 00 02 03` looks like a dibit/quadrant map. 141–1CF are smooth signed curves that resemble filter or AGC coefficient tables. | ROM bytes | Shapes are facts; their roles are hypotheses |

**Working conclusion:** the modem is very probably a V.26 ter-class 2400 bit/s
duplex echo-cancelling modem (1800 Hz carrier, 1200 baud, 4-phase DPSK, 100%
raised cosine split between Tx and Rx). The 8031 handles the DTE, scrambling,
the V.25/V.26 ter handshake and the front panel. That leaves the Am2901 board
with the sample-rate work: **DPSK modulation with pulse shaping, demodulation
(AGC, carrier/timing recovery, differential decision), and adaptive echo
cancellation**. The four MCM93422 RAMs on DSC 3557 (256×4 each) fit an
echo-canceller delay line and tap store. I'd put this conclusion at about 75%.
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
- **A3 Characterise the Am27S31 regions as DSP tables.**
  - Fit 141–1CF against raised-cosine and root-raised-cosine pulses at 8 (and
    4, 6, 12) samples/baud, Hilbert/interpolator taps, 1/x, log/exp and AGC
    curves.
  - Test 68–6F against the V.26 ter Table 1 Gray mapping (00→0°, 01→90°,
    11→180°, 10→270°).
  - Interpret 30–7F as parameter blocks, e.g. phase increments: 48 = 1800 Hz
    and 56 = 2100 Hz per 256-step phase at 9600 Hz; byte 0x34 = 0x30.
  - Record negative results as well.
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
  - a SAR-style 8-iteration loop that writes the DAC and tests an external
    condition. That would test the hypothesis that the receive ADC is
    DAC0830 + comparator.

  Mappings that cannot express the transmitter's minimum operations are
  dropped. *This is the key change:* fields get scored by algorithmic meaning
  rather than statistical plausibility.
- **A5 Cycle budget.** For microcycle = 14.4 MHz / k (k = 1…4), compute the
  microinstructions available per 9600 Hz sample and per baud. Compare these
  with loop lengths in the listing. The main loop must close in a whole
  number of samples.

### Phase B: physical evidence from the owner (small, decisive)

Listed in order of value per effort:

- **B1 Trace USART 01/05 pins** (TxD, RxD, TxC, RxC, SYNDET, RTS/CTS) and the
  mode-0 shift-chain outputs to their destination board/connector pins. This
  settles E2 and A2.
- **B2 About 25 unpowered continuity checks on DSC2847:**
  - 8X02 AC0–2 and TEST;
  - the latches at positions 5/6/29/30 → Am2901 I0–I8, A0–3, B0–3, Cn, D-bus
    source;
  - DAC0830 WR/XFER and the comparator (if any) on DED 3558;
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
  sequences, DAC sample spectra, bit decisions), not as a bit-exact target.
- **C2 Transmit test.** Drive the surviving mapping(s) with the real
  controller's command frame for "data 2400" plus the synchronous scrambled
  bitstream from USART 01. Pass criteria:
  - the DAC sample stream has its spectral peak at 1800 Hz × (true sample
    rate / 9600);
  - the phase steps follow the dibits;
  - "segment 1" yields 180° reversals;
  - the 2100 Hz state yields a tone.
- **C3 Receive test.** Feed reference line samples through the identified
  input path and check that the recovered bits reach the USART-01 receive
  side.
- **C4 Echo canceller.** Feed the board's own transmit signal back as echo
  and check that the residual falls while training is enabled and freezes
  when it is commanded off.

## 3. Acceptance for the question

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
