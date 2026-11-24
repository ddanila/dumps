# G2: establish the modem function by execution

This work follows [PLAN-2.md](../PLAN-2.md). G1's assumption-driven executor
and annotations are tools for this goal; their acceptance does not establish
G2. The required end result remains a controller-driven microcode transmitter,
plus a demonstrated receiver or echo canceller, with the modem functions
identified in the routines.

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
has exact sine and direct Gray-map constraints; coefficient fitting remains.
A4 has a numerical target but no demonstrated modulator. A5, C1's complete
reference model, C2 and C3/C4 remain outstanding. Hardware checks in phase B
have not been performed. G2 remains active; the ≥80% identification threshold
and the execution acceptance criteria have not been met.

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
carries information that a single frame cannot supply. A continuous call
simulation and the line-side/DSP connection are still required for A1/A2.

The [composed receive/state probe](receive_state.py) executes the unchanged
8031 input routine at 0800 with seven synthetic USART receive completions,
then executes the A2 state step on the **same CPU and RAM**. It sweeps all 256
values of the fifth payload byte. The input routine stores that byte in RAM2E;
on expired A2, every value with bit 6 clear leads to B8, and every value with
bit 6 set leads to A3. All 256 runs reach the common state-step exit without
emulator errors. This proves that a received frame bit controls the fork, but
the frame's physical source and the two states' modem meanings are not yet
known. The handoff between the local routines is still harness-directed.
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
