# G2: establish the modem function by execution

This work follows [PLAN-2.md](../PLAN-2.md). G1's assumption-driven executor
and annotations are tools for this goal; their acceptance does not establish
G2. The required end result remains a controller-driven microcode transmitter,
plus a demonstrated receiver or echo canceller, with the modem functions
identified in the routines.

The [DED3558 photo and datasheet review](ADC0800-INPUT.md) identifies a
stickered ADC0800PCD as a candidate source of complementary 8-bit receive
samples. An earlier description of that photographed converter as a DAC0830
was incorrect. The output converter and both sample-bus routes remain to be
identified; existing DAC0830 executions are diagnostic counterfactuals.

The [ADC sample run](ADC-SAMPLE-RUN.md) feeds 256 complementary reference
line-sample bytes to the recurring D read at 38E under the photo-constrained
q3 mapping. All samples are consumed, but the observed post-dispatch state
depends only on the current byte, even when sample order is reversed. This
rules out that **scoped path alone** as the demonstrated differential receiver;
other input routes and state locations remain open.

The [photo-informed board experiment](../board/PHOTO-HYPOTHESES.md) revisits
the physical-wiring blocker: missing proven nets do not prevent explicit
candidate wiring from being executed. It runs the real control PROMs through
the chip models, preserving unknown startup data, and screens control-source
and indirect-branch alternatives. This reopens hypothesis testing; it does not
yet satisfy G2's functional acceptance checks.

The subsequent [photo field constraints](PHOTO-FIELDS.md) identify three
candidate U6→U2 B-address routes and introduce four A/B-swapped instruction
variants. This also uncovered and corrected a cross-mapping operand-selection
bug in the ROM-read screen, reopening loop candidates that were previously
excluded. The new variants and corrected screen remain hypotheses to test
against the full transmitter/receiver requirements.

The [photo-swapped ROM-loop runs](SWAPPED-ROM-LOOPS.md) exercise two of those
reopened paths. In q3, real quarter-sine bytes affect the recurring 392–395
output quartet, but each reset fixture repeats one constant quartet. In q2,
eight diagnostic ROM gates sustain a D-fed loop at 127, yet its value settles
after the first transition. Four other gates sustain a D-fed loop at 12C that
also settles. These results narrow the tested assumptions; they
do not demonstrate a phase accumulator or a controller-driven waveform.
The photo-compatible fitted mapping has a separate ROM-fed path at 299: all
48 diagnostic ROM gates that select it make two to five reads with changing
addresses, but [the executed sweep](SWAPPED-ROM-LOOPS.md#fitted-mapping-changing-rom-addresses-lead-through-a-finite-drain)
reaches no candidate output word under its D=FF startup fixture.

A newer [q1 photo-constrained run](SWAPPED-ROM-LOOPS.md#new-photo-constrained-q1-loop-an-exact-20-value-rom-recurrence)
does sustain changing ROM data at 12C. It iterates the previous ALU result
through the upper Am27S31 bank and enters an exact 20-value cycle after eight
reads under all 16 tested ROM gates. This is a computed recurrence in the
declared emulator fixture, but it has no demonstrated phase increment,
controller-symbol dependence or DAC connection. The matched q2 cases instead
settle to fixed points or a two-value alternation. In the q1 fixture, BLT at
12F exits when the preceding value is zero; 245 of 256 possible ROM-feedback
byte states instead enter the same 20-cycle attractor. The observed initial
state is one of those 245, which further cautions against calling this a
modem carrier.
The alternative lower-ROM-bank fixture reads zero at 12C and exits at once;
all 256 possible lower-bank feedback states reach zero within ten steps. The
bank-select wiring is unknown, so this comparison identifies a useful
terminating candidate rather than the board's actual mode.
A site-specific four-case test shows that the 12C bank alone determines the
immediate exit in this fixture; changing the 127 bank has no effect because
both candidate bytes there are zero. The exit path later parks at 084.
All 256 diagnostic bytes at the early D read at 002 were also executed under
both 12C bank choices. They change the ALU result at 002 but never reach the
07C–07F phase map or 392–39F candidate output sites; each bank retains its
same exit or loop outcome. [The saved sweep](SWAPPED-ROM-LOOPS.md#new-photo-constrained-q1-loop-an-exact-20-value-rom-recurrence)
narrows this fixture without identifying the physical input source.

The [controller-bit dispatch experiment](CONTROLLER-BIT-DISPATCH.md) takes
128 scrambled bits computed by the unchanged 8031 ROM and supplies them, under
an explicit candidate connection, to the recurring D-consuming word 38E in
one continuous DSC2847 run. The following dispatch at 38F follows every bit,
but its 0 and 1 entries yield equal output quartets in all 65 tested
quarter-sine phase fixtures. Its retained state after each group is likewise
identical across the 128-bit run. This exercises a controller-derived input stream
without establishing a modulated line signal or the physical input route.
The [main-loop-to-DSC bridge](MAIN-LOOP-DSP-BRIDGE.md) replaces that local
scrambler stimulus with four real 8031 main-loop USART byte streams and their
concatenation. Under the photo-constrained D38E hypothesis, all 448 bit
presentations are consumed, but the candidate ALU group and post-group state still
depend only on the current bit. No ROM read follows the recurring dispatch.
A whole-loop scan finds only the D38E input arithmetic varying in ALU Y;
the other 15 recurring PCs each emit one fixed Y value. This narrows the
same candidate path without establishing a transmitter.
The [five-mapping controller screen](PHOTO-MAPPING-STREAM.md) applies the
photo A/I constraints to q1–q4 photo-swapped and fitted-swapped mappings.
At Q=5 all consume 128 controller-derived bits, but none repeatedly reads
the ROM or changes a candidate output after the input. This excludes the
same scoped path under a broader set of field choices; startup and command
routes remain to be tested.

The [084 command probe](TERMINAL-COMMAND.md) tests a separate continuation:
an explicitly hypothetical AC=RST pulse on the 8X02 command pins at the
terminal word. Fifteen such pulses produce clean, stack-preserving restarts
of the real-PROM q3 Gray-operand path, but only six candidate output visits.
A changing D316 fixture yields alternating Y values 10 and 34, with no
demonstrated phase accumulation or physical output route. The datasheet
offers no dedicated runtime reset pin; the command override has no traced
board circuit and remains a diagnostic alternative. A whole-path ALU scan of
the matched held/changing fixtures finds identical control flow over 1,900
cycles and confines input-dependent Y values to ten sites, giving specific
alternatives to 392 for future output-net checks.

The [PROM-enable timing sweep](PHOTO-ENABLE-TIMING.md) tests candidate U10 E2
and U11 E4 latch levels across all initial Q bytes. The only same-phase valid
read combination reaches 38E from 32 seeds but gives no recurring ROM reads
or changing candidate output in the controller-bit run. An E2-high diagnostic
opens recurring reads only by assuming U10 data remains available while the
PROM is disabled. This points to an explicit latch-hold or phase model for
the next experiment; the present counterfactual is not a recovered board path.
A follow-up split test shows that I0 high opens those reads, while A1 high
alone does not. This narrows the wiring or timing hypothesis to I0 without
turning the conflicting same-phase fixture into evidence of a transmitter.
The board-engine capture-edge check finds that a simple U10→U5 route cannot
latch E2 high together with valid U10 data on one edge; it explicitly yields
high-impedance data bits instead. A different I0 route or a real hold circuit
would be needed to turn that diagnostic path into a board candidate.
An eight-bit U10 source screen finds that only a hypothetical U10 bit-0 feed
to U5 D0 sustains ROM reads under a read-valid E2 level, and even that path
settles to fixed addresses and candidate outputs. The source is untraced.

A later [photo-constrained candidate](PHOTO-FIELDS.md#photo-constrained-startup-and-controller-bit-run)
changes A2/A3 and fixes two possible latch-enable inputs. With initial Q=5,
it consumes the same 128 controller bits and gives distinct but fixed ALU
quartets for 0 and 1. All 32 startup Q values that reach this dispatch were
tested with repeated bits; none develops changing output. A full byte sweep
shows that 38E stores `D−Q` and 38F selects one of four groups from it, with
no earlier-value dependence in the observed post-group state. None of the
137 diagnostic ROM gates adds a repeated Am27S31 read to this path. These
executions sharpen the path's behavior but still do not identify the real D
source, DAC connection or modem function.

## First independent ROM constraint

[ITU-T V.26 ter (11/88), §2.5.2.1, Table 1](https://www.itu.int/rec/dologin_pub.asp?id=T-REC-V.26ter-198811-I!!PDF-E&lang=e&type=items)
assigns differential phase changes 0°, 90°, 270°, 180° to dibits in binary
index order 00, 01, 10, 11; the first bit arrives first. In a 16-position phase
representation these increments are **00, 04, 0C, 08**.

The unmodified Am27S31 dump contains that exact four-byte sequence once,
at **07C–07F**. This supplies a more specific transmit-encoder candidate than
the proposed 068–06F region. The two four-byte blocks there are 0,1,2,3 and
1,0,2,3: neither directly matches the quarter-turn map 0,1,3,2. This rejects
those direct interpretations only; an unknown input/output permutation could
still give them another role.

The same dump supplies an exact rounded 127-amplitude 16-point sine at
000–00F and five wrap samples at 010–014. The 65 bytes at 100–140 exactly
match the first quarter of a 256-point sine, including both endpoints. These
are numerical identities, independent of the six microcode mapping choices.
They do not by themselves identify the standard or the physical ROM wiring.

The [pulse-family fit](pulse_fit.py) tests the predetermined signed window
16F–1CF (97 bytes) as one contiguous raised-cosine or root-raised-cosine
impulse. It searches 4, 6, 8 and 12 samples/symbol, roll-off 0.05–1.00,
quarter-sample center positions, and freely fitted scale and offset. The best
R² is only **0.358** for raised cosine and **0.332** for root raised cosine,
both at 12 samples/symbol; at eight samples/symbol they are 0.234 and 0.203.
This rejects those *simple contiguous-window* interpretations. It says
nothing decisive about split, polyphase or transformed tables, whose indexing
and physical clock are still unknown. The [report](results/pulse-fit.json)
retains the full signed bytes, search domain and fit parameters.

The adjacent 141–16E segment is a separate monotone 46-byte decline from
30 to 13, ending just before the signed jump to −8 at 16F. A
[scoped shape comparison](decay_fit.py) gives affine exponential R² 0.982,
reciprocal 0.980, inverse-square-root 0.979 and logarithm 0.978, versus
linear 0.945. The best exponential reproduces only 28/46 rounded bytes, and
the near-tied smooth families do not identify an AGC or filter table. The
[saved fit](results/decay-fit.json) records the scan and source hash.

The [runner](table_signatures.py) verifies the acquisition hash, scans every
possible four-byte start, checks both sine identities, and computes reference
phase trajectories from the stored 07C bytes. Repeated dibit 11 yields
alternating half-turn phases for 32 symbols, a target signature for segment 1.
The sample calculation with phase increment 3 at an assumed 9600 samples/s
has frequency 1800 Hz. **These are reference calculations, not executed
microcode or observed DAC output.** They do not count as C2 success.

The [saved report](results/table-signatures.json) includes the exact search
results, negative candidate comparisons, reference trajectories, source hash
and limitations. Tests cover differential accumulation across every initial
phase, repeated reversals, altered-ROM rejection and the last search window.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/table_signatures.py
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode/g2 -v
```

## Next evidence and acceptance status

### Independent signal reference for phase C

The [reference modem](reference_modem.py) generates diagnostic expectations
without executing DSC2847 microcode. It differentially encodes dibits using
the independently identified 00/04/0C/08 phase steps, shapes symbols with a
100% raised-cosine pulse at eight samples/baud, and quantizes the 1800 Hz
carrier to signed 8-bit PCM. Its 80-symbol steady carrier peaks at exactly
1800 Hz in a 15 Hz DFT bin; a separate answer-tone fixture peaks at 2100 Hz.
Thirty-two repeated `11` dibits alternate the 16-step phase between 8 and 0.

A known-carrier matched-filter receiver recovers an 80-symbol randomized
diagnostic stream with zero dibit errors. An integer Q15 normalized-LMS
reference reduces a synthetic two-delay echo's residual RMS from 5.15 to
1.64 in the sampled training windows; its coefficients freeze after training.
The [saved signatures](results/reference-modem.json) and tests provide concrete
comparisons for future C2–C4 microcode runs. The pulse coefficients and
receiver are floating-point diagnostics around 8-bit PCM, so this is **partial
C1**, not a bit-exact fixed-point hardware model. No board mapping, actual
sample rate, DAC waveform, recovered USART bits or echo-canceller routine is
established by this reference.

The [C2 bridge check](c2_bridge_check.py) applies the first necessary transmit
gate to both saved controller-to-DAC candidate runs. Each executes real
microcode under its declared q3 routing and generates 17 DAC transfers at
cycles 55, 67, …, 247. One run transfers code 34 every time; the other code
146 every time. Both have zero changing-sample energy, whereas the reference
1800 Hz fixture uses 29 different PCM codes. Thus **this particular bridge
fails C2** before spectrum or phase tests. The [report](results/c2-bridge-check.json)
records the exact codes, cycles and artifact hashes. Since its byte routing
and DAC strobe are hypotheses, this failure does not reject other mappings or
physical output paths.

### Additive-instruction screen

Across the six existing datapath profiles, 62–82 used words per profile decode
as an addition with an external D operand and a retained Q or RAM destination.
This is a capability screen, not evidence that D comes from the Am27S31 at
those words. The prominent repeated candidate, 36C–36E, writes three successive
RAM registers. In the q3 reset run with the declared upper-bank ROM gate, its
checked recurrence uses ROM data, an external reply and carry to choose whether
to repeat. R0 and Q remain fixed; the next ROM address comes from an old
register value on Y. This is a ROM-address/carry wait, not demonstrated phase
accumulation. See the [exhaustive recurrence study](../assumed/ROM-CARRY-REPLIES.md).

A [stricter direct-accumulator screen](phase_add_screen.py) requires a single
word to add D to Q and write Q, or add D to RAM[A] and write the same register.
It finds 23/23/21/20 candidates in q1/q2/q3/q4 and none in the two fitted
profiles. This **does not eliminate** the fitted profiles: a phase update can
take multiple words or use another operand source. In four saved q3 runs,
including the long ROM/carry feedback run and both controller-frame bridge
traces, only 002 and 076 among these candidates are reached, once each during
startup. No direct candidate repeats in those particular runs. The [report](results/phase-add-screen.json)
records every candidate, visit, and mapping/trace digest.
The declared q3 stack-aware control-flow graph has 1,395 states and 45 cyclic
components; none contains one of those 21 direct candidates. This graph includes
both outcomes of conditional transfers but only its declared dispatch tables.
It excludes a *single-word* D-driven phase-add loop under that scenario, not a
multiword phase update or a different hardware control-flow decode.

The [ROM-cycle screen](rom_cycle_screen.py) intersects the same stack-aware q3
graph with the previously fitted two-bit ROM-read gate. Only three distinct
cyclic shapes contain a word selected to receive ROM data on D: 02B–02E,
1EC–1ED and 36C–36E. At 02C the D addition does not load a register (though
its flags could affect later words); 1EC overwrites R3 from R4 and D before a
two-word poll; the 36C–36E address/carry recurrence is characterized above.
The [saved screen](results/rom-cycle-screen.json) includes all decoded
operations and source hashes. **The gate is a diagnostic fit, not physical
wiring.** This rules out a demonstrated modulator only in this gate/mapping/
dispatch combination; it does not eliminate other ROM-read policies or
multiword phase logic.

Existing execution studies narrow two of these static cycles further. In
[1,024 q3 early-entry reset runs](../assumed/EARLY-ENTRY22.md), 02B is visited
once before control reaches a different wait at 05D; the apparent 02B–02E
cycle is an overapproximation for those inputs and previous-flag timing.
At [1EC–1ED](../assumed/HANDLER-REPLY.md), the repeated D read is a checked
equality poll: R4 and Q remain fixed while each reply overwrites R3. Neither
run demonstrates phase progression. This leaves the already characterized
36C–36E recurrence as the only exercised ROM-fed cycle among these three
under its diagnostic gate, and that recurrence does not generate a waveform.

The [family-wide screen](all_rom_gate_cycles.py) repeats the intersection for
**all 137** gates that fit the original diagnostic ROM-read labels. Seventy-three
select no D-consuming word in any cyclic q3 component. None selects a D
operand in the recurring paired-output loop 38C–3A1. Across the other gates,
only 1EC, 36C and 36E combine a cyclic D read with a register write **in q3
and q4**; those sites are the poll and carry recurrence above.

**Correction:** the earlier claim that all six mappings shared those three
sites was wrong. The screen reused operand-selection results cached under q3.
Recomputing D selection for each mapping additionally admits **05E, 061, 127,
12C in q1/q2**, and **187, 299, 29B, 29C in both fitted mappings**. These are
renewed candidates for runtime experiments, not established oscillators. The
[corrected result](results/all-rom-gate-cycles.json) preserves the mapping-specific
operations and counts; regression tests detect reuse of another mapping's
operand selection. A ROM operand may also be captured before a loop, so the
screen does not exclude every possible modulator algorithm.

The [photo-constrained 05D–063 run](PHOTO-05D-LOOP.md) now tests the first
two renewed q1 sites. No initial Q byte in the declared reset fixture reaches
them. A diagnostic direct entry makes 05E and 061 read the same Q-indexed ROM
byte repeatedly while Q stays fixed, under either bank. This narrows that
local loop without ruling out a caller that changes Q or another mapping.

The [reset-driven ROM shift-wrapper run](ROM-SHIFT-WRAPPER.md) tests the
fitted-original 299 and 187 candidates with real Am27S31 bytes. Under one
diagnostic read gate, all 1,024 combinations of D byte, ROM bank and two
dispatch seeds return through the wrapper, then wait at 084. Q drains to zero
and the ROM base byte is zero; this explains the loop exit without revealing
a retained phase, line output or receiver function. Two of 12 broader gate
fits divert sampled inputs earlier, so the enable route still matters.

The screen therefore does not identify a transmitter. The next discriminating
search must combine a *reached* D-add instruction with independently supported
ROM selection, dibit-derived address and retained phase across symbol periods.

The next discriminating question is whether a candidate mapping can derive
07C plus the real line-side dibit, add the returned phase increment to retained
phase, and then address the sine table. The index must arise from microcode
state and controller data; inserting that sequence into a scenario would only
reproduce the reference calculation. Actual control-flow and ROM-address
traces are needed before naming a transmitter routine.

A1/A2 controller state and command identification remain outstanding. A3 now
has exact sine and direct Gray-map constraints plus scoped pulse and decay
fits; the remaining table roles are unidentified.
A4 has a numerical target but no demonstrated modulator. A5, C1's complete
reference model, C2 and C3/C4 remain outstanding. Hardware checks in phase B
have not been performed. G2 remains active; the ≥80% identification threshold
and the execution acceptance criteria have not been met.

The [unpowered continuity worksheet](PHYSICAL-CHECKS.md) gives exact U9,
control-PROM and LS374 pin pairs that would directly constrain the sequencer
command, test, address and clock nets. It records no measurements; the current
[board ledger](../board/nets.json) still has zero complete nets.

## Executed lower-bank operand test

[The Gray operand probe](gray_operand_probe.py) reuses the q3 path that was
already shown to read the Am27S31 at microinstruction 317. It changes the
declared bank to zero and sets the diagnostic input at 316 so previous Y
addresses 07C–07F. Each run starts from zero RAM/Q, executes the real control
store, and logs the actual ROM address, operand and ALU output.

| Input dibit label | ROM address | ROM byte | First Y at 392 | First terminal 084 |
| --- | ---: | ---: | ---: | ---: |
| 00 | 07C | 00 | 10 | cycle 110 |
| 01 | 07D | 04 | 18 | cycle 110 |
| 10 | 07E | 0C | 34 | cycle 110 |
| 11 | 07F | 08 | 26 | cycle 110 |

The 160-instruction traces make exactly one ROM read and one visit to output
word 392, then repeat at terminal 084. Changing the ROM byte changes that
single output by twice the byte value. There is no phase accumulation or
sample stream in this scoped path. Its address input comes from a diagnostic
D316 value; the real controller line-side bitstream was not connected. Thus
this candidate path does not satisfy the transmitter test, even though it can
consume the exact Gray-map bytes.

The [report and four full traces](results/gray-operand-probe/report.json)
preserve the outcomes and source hashes. Reproduce them with:

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/gray_operand_probe.py \
  --out /tmp/nokia-g2-gray-operand
```

The next mapping search should require repeated ROM accesses whose address
comes from actual controller dibits and whose retained state carries phase
between symbols. This probe rules out only the declared q3 reset scenario.

## Controller state-to-frame constraint

The [executed octet-classifier study](PATTERN-CLASSIFIER.md) identifies a
state-dependent detector reached from controller states 83 and A6. On local
entry it marks 40 of 256 received-octet candidates in state 83 and 16 in A6,
including single-one and adjacent-pair patterns. Its relationship to the
V.26 ter rate-pattern rules is not yet established.

[The controller frame sweep](controller_frames.py) executes the unchanged 8031
ROM from 1EE2 through actual output construction and four-byte transmission
for every one of the 256 possible RAM34 state values. A single fixed diagnostic
fixture holds the flags, received payload, prior outputs and counters constant.
Every run completes all four transfers and the later P1.2 latch; transmitted
bytes match the independently checked `output_build` reference.

Only **38 distinct wire frames** result from the 256 states in this fixture.
For example, A0 and A2 both send `80 02 88 7A`; C2 and C3 both send
`D8 42 81 A2`. States 40–7F all send `80 02 00 FA`. The upper five bits of
the fourth byte come from the ROM state-code tables for 80–BF, a constant for
C0–FF, and zero for 00–7F. Thus the fourth byte is a compressed state code
plus flags, not an invertible copy of RAM34. The other three bytes also depend
on state, flags, payload and prior values; a frame cannot be interpreted from
RAM34 alone.

This is a controlled sensitivity test, not a mapping from controller states to
V.26 ter roles. It narrows A2: the command interface needs state transitions
and the changing firmware variables, as well as the four-byte output. The
[full 256-state report](results/controller-frames.json) retains every frame,
source classification, collisions, execution checks and source hashes.

The [state/frame cross-check](STATE-FRAME-CROSSCHECK.md) places selected
executed countdowns, expiry successors and transmitted frames side by side.
A0 and A2 both send `80 02 88 7A` in the fixed frame fixture despite
different countdowns and successors. The state-step and frame runs have
different initial RAM fixtures and do not constitute one continuous call.
The newer [preserved-RAM chain](STATE-FRAME-CROSSCHECK.md#preserved-ram-chain)
executes four consecutive expiry/send pairs on one controller image. Across
all 256 injected RAM2E values it has four distinct chains, selected by bits
6 and 0; this confirms the A2 branch and outgoing frame dependence after
earlier output routines have modified the same RAM.
The [uninterrupted main-loop probe](MAIN-LOOP-CHAIN.md) goes further: eight
complete polling iterations receive and decode bytes, update state, send a
frame and follow the ROM's loop back to 1ED3 without PC handoffs. Across all
256 values of the received selector it produces six state/frame chains. Its
explicit timer and serial stubs still leave physical command meaning open.
With transmit-ready status supplied, the [continuous serial probe](MAIN-LOOP-SERIAL.md)
also records the controller's external port-01 bytes over 12 iterations for
every selector. All bytes match an independent bit-serial scrambler using the
recorded RAM37 input and history. Four distinct line-byte streams result;
selector bit 6 changes the state/source sequence, while bits 5 and 4 select
the 18- or 5-bit scrambler tap. These are usable controller-derived stimuli
for a DSC2847 connection hypothesis, not a recovered physical link.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/controller_frames.py \
  --out /tmp/nokia-g2-controller-frames.json
```

## A0–A2 controller state steps

[The local state-step probe](state_transitions.py) executes the unchanged
controller ROM from 1000 to the common exit at 1755. It starts with a qualified
state (`RAM22.4=1`), a controlled changed-input flag (`RAM24.5`) and timer high byte
(`RAM17`). It does not skip the dispatch code or write a result state itself.

| Entry state | With `RAM24.5=1`: countdown reloaded | With `RAM24.5=0` and `RAM17.7=1`: next state |
| --- | ---: | --- |
| A0 | 070D = 1805 | A1 |
| A1 | 0A2D = 2605 | A2 |
| A2 | 003C = 60 | B8 if RAM2E.6=0; A3 if RAM2E.6=1 |

When neither timer condition holds, each state remains unchanged. If the
qualification bit is absent, the code resets all three entry states to 00
before their state-specific branch; those negative controls are included.
The 13 executions in the [report](results/state-transitions.json) preserve
visited instruction addresses and each resulting timer/state value. The
extra A2 case executes the bit-76h branch in the actual ROM (`RAM2E.6`),
which selects A3 on expiry; the zero-bit control selects B8. The
counts 1805 and 2605 fit the timing windows proposed in PLAN-2, but these
local steps do not establish the timer's physical tick or name the stages
“silence” and “2100 Hz tone.”

Under the fixed controller-frame fixture above, A0 and A2 transmit the same
four bytes despite their different timer loads. The state trajectory therefore
carries information that a single frame cannot supply. The later continuous
polling-loop probe tests that interaction under synthetic peripheral events;
the line-side/DSP connection is still required for A1/A2.

The [composed receive/state/output probe](receive_state.py) executes the unchanged
8031 input routine at 0800 with seven synthetic USART receive completions,
then the A2 state step and four-byte output routine on the **same CPU and RAM**.
It sweeps all 256
values of the fifth payload byte. The input routine stores that byte in RAM2E;
on expired A2, every value with bit 6 clear leads to B8, and every value with
bit 6 set leads to A3. The resulting outgoing frame is exactly:

| Received RAM2E bits 6, 0 | Next state | Output bytes |
| --- | --- | --- |
| 0, 0 | B8 | D0 42 81 22 |
| 0, 1 | B8 | C0 42 81 22 |
| 1, 0 | A3 | D0 42 81 BA |
| 1, 1 | A3 | C0 42 81 BA |

All 256 runs complete all four transmissions and reach the output routine's
return without emulator errors. The other six bits have no effect in this
fixture. This proves a received frame controls both the state fork and two
outgoing control bits; the frame's physical source and the states' modem
meanings are not yet known. The handoffs between local routines are still
harness-directed.
The [saved sweep](results/receive-state.json) records each result and source
hashes.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/state_transitions.py \
  --out /tmp/nokia-g2-state-transitions.json
```

## State-byte timer matrix

[The full state-step matrix](state_matrix.py) runs the same unchanged 8031 ROM
for all 256 RAM34 values, once with the changed-input reload flag and once
with a negative high timer byte. All 512 bounded runs reach the common 1755
exit without a core error. The [report](results/state-matrix.json) retains
entry state, resulting state and countdown, visited instruction addresses and
source hashes. The matrix is a sensitivity map: arbitrary RAM34 bytes are not
necessarily reachable during a real call.

In the tested path, the A0→A1→A2→B8 expiry chain has reload values
1805→2605→60→70. Other distinct loads include 250, 455, 580, 1000 and 2000.
Those figures support a staged handshake hypothesis, but assigning particular
V.26 ter tone or silence names requires the actual output and line behavior at
each stage. Branches depend on other firmware flags too; the matrix holds
those inputs at zero.

The Timer 1 handler reloads `FC21`. At 11.9808 MHz and 12 oscillator clocks
per machine cycle, its 991 counts last **0.9926 ms before overflow**. The time
between software counter decrements also includes interrupt and reload
latency. Plan 2 now states “approximately 1 ms” rather than treating the
countdown values as exact milliseconds.

The [timing alignment](sequence_alignment.py) compares seven executed reload
counts with the windows in [ITU-T V.26 ter (11/88), §§6.3.1.1–6.3.1.3](https://www.itu.int/rec/dologin_pub.asp?id=T-REC-V.26ter-198811-I!!PDF-E&lang=e&type=items).
At a nominal 1 ms software tick, all seven selected counts fit their candidate
windows: A0=1805 for 2.15±0.35 s silence, A1=2605 for 3.3±0.7 s tone,
A2=60 and B8=70 for 75±20 ms silences, A7=250 for 250±5 ms silence,
AA=580 for a *combined* 500±50 ms tone plus 75±20 ms silence, and AB=25
for 25±3 ms silence. A6=2000 also resembles the specified 2 s rate-pattern
timeout but is unscored because the standard gives no tolerance window.
Using only the hardware reload-to-overflow period puts A0 and A1 just below
their lower bounds (1791.6 and 2585.7 ms); actual interrupt overhead is
unmeasured. These are selected timing matches, **not stage identifications**.
The [report](results/sequence-alignment.json) records both clock calculations,
standard windows and local expiry successors.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/state_matrix.py \
  --out /tmp/nokia-g2-state-matrix.json
```

## Microcycle budget and the G1 DAC loop

[The timing comparison](cycle_budget.py) reads the six completed G1 bridge
transactions and their saved microcode traces. Each reaches output word 392
at cycles 55, 67, 79, …, 247: a repeated DAC transfer every **12
microinstructions**, with a constant held code for each frame. The
oscillator marked on DSC2847 is 14.4 MHz; the divider feeding the sequencer
has not been identified.

| Assumed divisor from 14.4 MHz | Microinstructions per 9600 Hz sample | Unpaced 12-cycle transfer rate |
| ---: | ---: | ---: |
| 1 | 1500 | 1.2 MHz |
| 2 | 750 | 600 kHz |
| 3 | 500 | 400 kHz |
| 4 | 375 | 300 kHz |

At 1200 baud, the corresponding budget is 12000, 6000, 4000 or 3000
microinstructions per symbol. If every modeled transfer represented one
sample at 9600 Hz, a divisor of **125** would be needed. Under the k=1–4
cases proposed in Plan 2, some additional output gating or a different
clock relationship would be needed. The observed G1 bridge by itself cannot
serve as the expected transmitter waveform: its two held codes do not change
and its unpaced transfer rate is far above the candidate sample rate.

These are conditional clock calculations, not a measured 8X02 clock or DAC
wiring. The [saved comparison](results/cycle-budget.json) records the source
hashes and exact frequency ratios.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/cycle_budget.py \
  --out /tmp/nokia-g2-cycle-budget.json
```
