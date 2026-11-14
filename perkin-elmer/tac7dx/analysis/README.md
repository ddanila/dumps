# TAC7/DX firmware analysis and execution

Analysis date: 2026-11-14. Images: U35 `N5208003`, U36 `N5208004`, both
labelled 1999. The firmware identifies itself as **`TAC7,N5208003REVA`**.

The two dumps form a working Motorola 6809 program: 16 KiB from U35 and
32 KiB from U36. Both embedded ROM checksums pass. The original program
boots through all seven startup tests and reaches its service loop when
given synthetic peripherals. Its command parser and one complete periodic
interrupt have also been executed. This is a reproducible firmware harness,
not a complete emulation of a connected thermal-analysis instrument.

## What the board does

The TAC7/DX is the embedded controller between a host computer and a
thermal-analysis instrument. The manufacturer's TGA 7 documentation describes
the TAC as controlling the analyzer and digitizing its detector output for
the host. The host runs the experiment software; the TAC performs local
control, acquisition, communication and diagnostics.
See the [manufacturer's thermal-analysis manual, TGA 7 chapter](https://www.mse.iastate.edu/files/2011/07/ThermalAnalysisManuals.pdf).

The recovered code matches that role. It selects instrument-dependent
callbacks, services analog input/output, collects counter values, stores
acquisition data in banked RAM, and processes commands from the host.
There are two serial interfaces and a separate diagnostic communication
path when startup fails. It is a bare-metal polling/interrupt program;
there is no evidence here of a general-purpose operating system or shell.

The instrument selector accepts values **1, 2, 4, 5 and 8**. Those values
select tables of routines and parameters. Their mapping to specific analyzer
models has **not** been established. The harness chooses type 1; that does
not identify the instrument originally attached to this board.

## Image integrity and memory map

U35's raw 32 KiB acquisition contains identical 16 KiB halves. The harness
maps its upper half, preserving the original capture. U36 maps in full.
The firmware adds every byte after the first two bytes in each mapped ROM,
modulo 65536, and compares the result with that leading big-endian word.

| ROM | CPU addresses | Stored checksum | Calculated |
|---|---|---|---|
| U35 | `4000–7fff` | `0415` | `0415` |
| U36 | `8000–ffff` | `1aa9` | `1aa9` |

This validates the contents against the firmware's own integrity checks,
in addition to the matching physical reads. It does not establish the exact
physical EPROM manufacturer/type or rule out undetected checksum collisions.

| Address | Function |
|---|---|
| `0000–07ff` | Nonvolatile RAM region; simulated initially as zero |
| `0800–27ff` | Working RAM |
| `3004–3007` | PIA: DAC data and timing/control |
| `3008–300b` | PIA: counter/input interface |
| `3010–3013` | PIA: instrument type, counters and analog control |
| `3020–3023` | PIA: comparator, multiplexer and control |
| `3040–3043` | PIA: status/control outputs, including diagnostic indication |
| `3080–3083` | Primary 2661 serial interface |
| `3100–3103` | Secondary 2661 serial interface |
| `3200`, `3201` | Select/deselect upper RAM bank |
| `4000–7fff` | U35, always visible |
| `8000–ffff` | U36, or 32 KiB SRAM when selected |

The hardware map comes from the
[manufacturer's technical drawings, PDF pages 7 and 9](https://www.artisantg.com/info/Perkin_Elmer_TAC7dx_Technical_Information.pdf),
with functional names refined from ROM accesses. Firmware also writes
`3000/3001` alongside `3200/3201`; compatibility with another board decode
is a hypothesis. The harness accepts both pairs.

Reset vector: `8002`; IRQ: `a56a`; NMI: `5b57`. SWI, SWI2, SWI3 and FIRQ
vectors are zero. NMI writes a status indication and loops. Initialization
copies the NMI vector into the upper RAM bank so it remains present while
that bank overlays U36.

## Startup and failure handling

Reset sets the stack to `1c80` and enters initialization at `9f47`. After a
delay, the code configures the PIAs and executes this diagnostic chain:

| Routine | Test | Observed successful return |
|---|---|---|
| `a0fc` | Both ROM checksums | A=0 |
| `6a15` | RAM patterns, including banked RAM | A=0 |
| `a158` | PIA register checks | A=0 |
| `a4cd` | Clock/timing input | A=0 |
| `a265` | Instrument selector | A=0, B=1 |
| `a524` | Analog comparator response to two DAC patterns | A=0 |
| `a28d` | Serial internal loopback, both interfaces | A=0 |

Each serial port transmits and receives `ABCDEFGHIJKLMNOPQRSTUVWXYZ` during
its loopback test. After initialization, execution reaches main loop `50cf`.
See [boot checkpoints](results/boot/io.tsv) and [serial trace](results/boot/serial.tsv).

Failure enters a diagnostic loop rather than the normal application. It
indicates the error through the output PIA and accepts a `%` followed by CR
on the primary serial interface. The harness exercised two failures:

| Injected condition | Check result | Reply to `%\r` |
|---|---|---|
| Flip bit 0 at CPU `4002` in emulated memory | ROM failure; diagnostic group 1 | `%,2,01\r` |
| Never assert synthetic clock flag | Clock failure; diagnostic group 3 | `%,6,FF\r` |

See [bad-ROM trace](results/bad-rom/serial.tsv) and
[missing-clock trace](results/missing-clock/serial.tsv). The disk ROM files
are unchanged. Diagnostic replies use a different format/context from the
normal `$%` command. The diagnostic dispatcher around `a354` also contains
individual hardware-test entries; these were not all exercised separately.

## Host protocol and command dispatch

The normal parser takes `$`, a case-sensitive command character, optional
comma-separated signed decimal arguments, then carriage return. Numeric
parameters are represented internally in three-byte fields at `18ed` and
`18f0`. Replies generally contain the command character, numeric fields
and CR. The identity response is textual.

The dispatcher at `5b5f` uses three parallel tables:

| Table | Address | Purpose |
|---|---|---|
| Validation | `5baa` | Check argument count, ranges and controller state |
| Action | `5c60` | Perform operation |
| Reply | `5d16` | Format response |

Each table contains 91 entries, covering ASCII `20–7a`. **53 entries have a
supported-command validator**. Unsupported entries use `a6c3`; `6a97` is
a shared no-op return. [commands.csv](commands.csv) lists every entry and
all three routine addresses, including unsupported slots. There are also
special stream-handling paths in the parser; table coverage is not a claim
to cover every possible protocol transaction.

The [64 command experiments](command-results.json) include all 53 supported
characters with no arguments, plus selected valid parameters and errors.
Each case starts from the same post-boot RAM/peripheral snapshot. These are
function-level tests: a request is placed in the firmware RX ring, the
original parser at `a831` is called, and its TX ring is inspected. A test-only
reset-vector override selects that entry, and a RAM sentinel receives the
return. They are not end-to-end host/UART timing tests.

| Request (all followed by CR) | Actual firmware reply | Meaning established |
|---|---|---|
| `$i` | `i,TAC7,N5208003REVA` | Firmware identity |
| `$I` | `I,1,0` | Configured instrument selector in this scenario |
| `$%` | `%,0,0` | Basic successful response |
| `$J` | `J,1000,0` | Read a numeric setting; physical units unresolved |
| `$J,100` | `J,100,0` | Set/read back that setting |
| `$J,-100` | `!,4,0` | Rejected range |
| `$2,1` / `$2,0` | `2,1,0` / `2,0,0` | Accepted binary setting |
| `$2,999` | `!,4,0` | Rejected range |
| `$=` | `=,30000,0` | Numeric setting; meaning/units unresolved |
| `$I,1` | `!,2,0` | Wrong argument count |
| `$~` | `!,3,0` | Unsupported command |
| `$S` | `!,5,1` | State/precondition rejection |
| `$[` | `!,5,4` | State/precondition rejection |

The error pattern is `!,class,detail\r`: observed classes are 2 for syntax or
argument-count problems, 3 for unsupported commands, 4 for ranges, and 5
for state/preconditions. This interpretation follows both validator code
and execution results; exact vendor terminology is unknown.

63 of 64 cases return to the sentinel. `$#` queues `#,0,0\r` but waits for
the TX buffer to drain at `aba9`, which this isolated parser test does not
do. That case is recorded as **not returned**, not as a completed command.
The synthetic `$l` result (`-34133`) is not a physical measurement.

Serial service at `a7d9` handles receive status, buffering, output and XON/
XOFF (`11`/`13`). The primary RX ring descriptor is at `0549`, data at `0550`;
the TX descriptor is at `0ba9`, data at `0bb0`. Main-loop routine `ac0e`
services secondary communication. Full host software compatibility, baud
timing and streaming transactions have not been tested.

## Acquisition and control implementation

The code is organized around the main service loop and periodic interrupt
work, with RAM-resident function pointers selecting instrument-specific
behavior. Initialization at `4057` loads callback/parameter tables from
regions including `c028–c06f` and `ad2f–ad9a` into RAM. Consequently, a
routine's effect may vary with the instrument selector and operating state.

| Routine/region | Recovered role and evidence |
|---|---|
| `50cf` | Main loop: parser, secondary communication and pending work queues |
| `5123`, `51d2`, `524e`, `52c1` | Work selected through RAM queue/control fields |
| `a56a` | IRQ entry: inspect PIA flags, acknowledge source, dispatch work, RTI |
| `a59c` | Periodic work: serial status, counter capture, callbacks, timing bookkeeping |
| `41f5` | Channel scan, serial servicing, analog routing and DAC updates |
| `41d7` | Invoke scheduled callback list starting at RAM `036e` |
| `57cf` | DAC/comparator successive-adjustment conversion steps |
| `57fe` | DAC tracking adjustment: comparator selects +1/-1, with endpoint checks |
| `5833` onward | Calibration/scaling arithmetic and saturated output calculations |
| `5462` vicinity | Store acquisition values in upper banked RAM |
| `8d20` | `$T` action: stop/start-related acquisition state and callbacks |

The IRQ service captures values through `3008`, `300a` and `3010`, pulses
control outputs, and saves a six-byte block at `1720`. It calls the analog
scan and indirect routines through `16a7` and `04d6`. A countdown at `171e`
reloads from `1955`; a further counter at `0b90` schedules callback work.

The scan uses channel-routing data at `190d`, a channel index at `0478`,
and a previous-result array at `0481`. Its wrap logic includes six input
slots. DAC output records at `155d` contain three bytes per slot; writes go
to `3004/3005`, with extra control bits at `3012/3013` and multiplexer control
at `3021`. The converter routines adjust DAC values according to the
comparator sign at `3020`, showing software participation in conversion.
The exact sampling cadence and physical transfer functions remain unknown.

The `$T` action accepts a binary argument subject to state checks. The zero
path clears acquisition flags and counters; the other path installs an
acquisition callback. Calling this acquisition start/stop is an inference
from those effects, not a recovered vendor command name. Numeric commands
must not be assigned temperature/rate/force units without further evidence.

### Executed periodic interrupt

The interrupt experiment restores the boot RAM, banked RAM and PIA state,
constructs a complete 6809 interrupt stack frame, sets a synthetic PIA
source flag and executes the original IRQ entry `a56a`. Its RTI returns to
the RAM sentinel. This tests the handler itself; it does not emulate an
external interrupt waveform or continuous acquisition.

Observed in [the IRQ trace](results/irq/io.tsv):

- Entry, periodic service, channel scan, RTI and sentinel are all reached.
- Countdown `171e` changes from 200 to 199.
- Schedule counter `0b90` changes from 0 to 1.
- Output slot `155c` changes from 0 to 1.
- The six-byte capture at `1720` changes, DAC/control writes occur, and six
  bytes of upper-bank RAM change.
- Reentrancy flag `1ac9` is clear on return and the stack is restored.

These are synthetic values, not valid temperature, mass or displacement
samples. In particular, the stubbed counter interface does not implement
the real external counters.

## Reproduction

Tested with Python 3 and Debian MAME **0.251**, executable
`/usr/games/mame`. No extra Python packages or proprietary monitor ROMs are
needed. Run from this directory:

```sh
python3 analyze.py
python3 run.py
python3 run.py --scenario missing-clock --seconds 16 --output results/missing-clock
python3 run.py --scenario bad-rom --seconds 12 --output results/bad-rom
python3 command_tests.py
python3 run.py --irq-test --seconds 1 --output results/irq
python3 verify.py
```

For an individual parser experiment:

```sh
python3 run.py --request '$i' --seconds 1 --output results/query-identity
```

`probe.lua` intercepts the memory space of MAME's existing `cpu09` machine
to use its MC6809 core (4 MHz oscillator configuration). A temporary,
all-zero `tavbug.bin` satisfies the carrier's ROM-file requirement; the
expected checksum warning concerns that dummy monitor, not the TAC dumps.
The TAC ROMs supply the executed code and reset vector. This is not a new
native MAME TAC7/DX driver, and underlying carrier-device behavior has not
been exhaustively excluded. No physical programmer or instrument is used.

The PIA model implements DDR/data selection and output latches. The serial
model implements ready status and internal loopback. A deliberately
synthetic clock flag appears after 110 polls, meeting the ROM test's accepted
range; it is not a time-domain model. The comparator responds to a fixed
DAC threshold. These assumptions make the observed boot possible and do
not establish hardware accuracy. Normal boot does not generate periodic
CPU interrupts; the separate IRQ experiment provides explicit coverage.

Boot and IRQ snapshots preserve low memory, ROM view, upper RAM, registers
and PIA state. The main [`disassembly.txt`](results/boot/disassembly.txt) is
a **linear** disassembly: embedded tables and padding also become apparent
instructions, and data can misalign subsequent decoding. Use the entry
addresses in this report/CSV when studying individual routines. Likewise,
generated `accesses.tsv` includes debugger/disassembler reads and is **not
execution coverage**; these large counters are omitted from Git. `io.tsv`
limits detailed I/O to the first 1,999 events; checkpoints
and sampled PCs remain available afterward.

## What remains unresolved

This analysis establishes integrity, architecture, startup, protocol dispatch,
selected commands and one acquisition/control interrupt. It does not fully
recover all 53 command meanings, all numerical algorithms, units,
calibration constants, instrument-type mappings or every state transition.
There is no original NVRAM/calibration acquisition in this collection.
The thermal plant, sensors, real counter hardware, continuous interrupts,
streaming and host software session are not emulated.

A more complete emulator would replace the synthetic devices with a native
board driver, identify the instrument selector wiring, recover persistent
calibration data, and compare host transactions and timing against a real
controller. The evidence here is enough to show that these ROMs constitute
a coherent functioning controller program and to provide a useful starting
point for that work.
