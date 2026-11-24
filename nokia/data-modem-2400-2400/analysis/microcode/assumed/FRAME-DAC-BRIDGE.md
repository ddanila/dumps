# A completion-qualified controller-to-DAC diagnostic transaction

*Runs under the [shared assumptions](ASSUMPTIONS.md).*

An explicit connection hypothesis now composes three existing models: the
actual 8031 output builder and transmitter, a zero-reset microcode execution,
and the DAC0830 digital buffers. The transaction starts only after the
controller's fourth transmit completion and P1.2 latch pulse. It then uses the
actual transmitted bytes as microcode inputs, reads the real ROM, and produces
repeated DAC load/transfer events from the running microcode.

This is an executable one-way diagnostic connection, **not recovered board
wiring**. The transport, input routing, startup request, ROM enable and DAC
strobes are all declared assumptions. No controller feedback or autonomous
phase progression is inferred.

## Controller execution and completion gate

Two fixtures are taken from the verified
[output-through-transmission study](../../controller/OUTPUT-SEND.md). Both use state
A0 with different saved application flags and data. The unchanged 8031 ROM
runs from 1EE2 through its actual calls to 006E and 0899, stopping at 1EE8.
There is no intermediate PC or RAM injection between building and transmitting.
The core and controller ROM are hash checked.

The resulting SBUF frames are, in hexadecimal:

```
frame-85: 85 02 98 7C
frame-05: 05 12 A8 7C
```

These are the bytes actually transmitted after the controller's 00,03,00,F8
XOR masks. The bridge does not undo those masks. It collects the four TX
values and their ordered completions, then accepts the frame on the rising
P1.2 edge. It requires that edge to occur strictly after completion four.
Submitting all four bytes without that completion is insufficient.

Synthetic serial delays of 8, 16 and 32 controller-harness ticks are tested.
The frame values remain identical while the latch times change:

| Frame | Delay 8 | Delay 16 | Delay 32 |
| --- | ---: | ---: | ---: |
| 85 | 381 | 413 | 477 |
| 05 | 560 | 592 | 656 |

Each complete controller run reaches 1EE8 with its original stack pointer and
no core error. Negative runs permit zero or three completions: the firmware
waits at 08B0 or 08D4 respectively, emits no latch pulse, and the bridge starts
no microcode run and generates no DAC event. A test also removes completion
four while preserving the later latch event; the bridge rejects that
inconsistent event history rather than accepting a premature frame.

## Declared byte routing

On acceptance, the external harness requests one fresh, zero-initialized
microcode run. This startup request is a bridge assumption, not a reset wire
recovered from the controller or an instruction inserted into its ROM.

| Transmitted byte | Microcode input read | Role in this hypothesis |
| --- | --- | --- |
| 0 | 002 | Initial Q contribution; 076 is explicitly held at zero |
| 1 | 316 | Adds to Q to form the preceding-Y ROM address byte |
| 2 | 118 | Captures the low component byte after the instruction's subtraction |
| 3 | 107 | Captures the high component byte after subtraction |

Every routed byte is supplied unchanged. The existing PLP-side early replies,
D=1 elsewhere, previous flags, q3 mapping, ROM read only at 317, and paired
entry zero are retained as separately labelled assumptions. The first frame
byte selects handler 5 through its low three bits; its full value remains in
Q. This is not a discovered command protocol.

Let the four wire bytes be c,p,l,h. The checked dataflow is:

```
Q = c
address byte = (p+c) & 255
S = ROM[256 + address byte]
U = (S+c) & 255
V = ((l-1)&255) + 256*((h-1)&255)
paired output = low/high of 2U, then low/high of (2V modulo 65536)
```

The ROM address is established at microcycle 44 and read at 45. The four
arithmetic outputs begin at cycles 55–58. Every later table call preserves
U, V and Q and repeats the same four values.

| Frame | ROM address | ROM byte | U | V | Output bytes |
| --- | --- | --- | --- | --- | --- |
| 85 | 187 | 0C | 91 | 7B97 | 22 01 2E F7 |
| 05 | 117 | 44 | 49 | 7BA7 | 92 00 4E F7 |

All entries in this table are hexadecimal. Address 117 lies in the identified
quarter-sine region; 187 does not. The latter is a real upper-bank byte, but
calling it a quarter-sine sample would be incorrect.

## Recurring DAC transfers and timing

The declared DAC connection takes ALU Y at 392, the first result's low byte.
Each occurrence pulses the input latch and then transfers it to the DAC
register through the existing level-actuated DAC0830 model. This uses the
`first_low` / `per_load` hypothesis in [DAC-OUTPUT.md](DAC-OUTPUT.md).

The last output high byte is F7 in both cases. Thus the actual loop at
38C–390 repeats with period 12 rather than returning to terminal 084. The
256-instruction run contains 17 DAC transfers at cycles 55,67,...,247.
Full-state recurrence independently verifies the period; repeated resets or
manually incremented phases do not generate these updates.

The held DAC code is constant: decimal **34** for frame-85 and **146** for
frame-05. Repeated transfer strobes are not evidence of a changing analog
waveform. There is one ROM read per transaction and no observed phase advance.

For cross-model timing, the scenario explicitly chooses four microcycles per
controller-harness tick and a two-microcycle startup latency:

```
microcode start = 4 * controller latch tick + 2
DAC transfer time = microcode start + 55 + 12*k
```

For delay 8, the first transfer times are 1581 and 2297 in these arbitrary
common units. Changing the serial completion delay shifts the start while
leaving the microcode trace, DAC code and 12-cycle update interval unchanged.
No oscillator frequency, analog settling time or physical sample rate is
claimed.

## Validation and limits

Six complete transactions cover two real controller fixtures at three serial
delays. Four incomplete-transfer controls cover the same fixtures with zero
or three completions. The report retains complete controller event histories,
ROM/core/source hashes, time mappings and dataflow predictions. Two microcode
trace directories and their DAC logs are shared across delays only after their
transition digests are verified identical.

Tests check completion/latch ordering, the unchanged frame-byte bindings,
selected ROM operands, recurring output timing and both expected DAC codes.
The consolidated plan validator re-executes the complete bridge and compares
all saved artifacts byte for byte, in addition to its existing long-run checks.

This supplies a coherent one-way transaction under the plan's explicit
assumption policy. It does not resolve physical routing, identify modem
modulation/demodulation. The [program overview](PROGRAM-OVERVIEW.md) connects
this experiment with the separately interpreted handler and helper bodies. A return protocol and autonomous waveform generation
remain unclaimed, rather than silently supplied by the harness.

[Configuration](frame-dac-bridge.json), [runner](frame_dac_bridge.py), and
[report](results/frame-dac-bridge/report.json).

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/frame_dac_bridge.py
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -p 'test_*.py'
```
