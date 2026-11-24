# Nokia Data Modem 2400/2400: hardware and firmware investigation

## At a glance

| Folder | Contents |
| --- | --- |
| [controller-810244e/](controller-810244e/) | 8 KiB 2764 from DSU 3556: the 8031 controller program |
| [microcode-810237c-810240c/](microcode-810237c-810240c/) | 4 × 1 KiB MMI 6381 PROMs from DSC 2847: the Am2901/8X02 control store |
| [am27s31dc-prom/](am27s31dc-prom/) | 512 B Am27S31DC: sine and lookup tables, probably 810241 on DSC 3557 |
| [photos/](photos/) | All 22 owner photographs, unchanged, with hashes |
| [analysis/](analysis/) | 8031 harness and controller studies; [microcode/](analysis/microcode/) holds the bit-slice work |

**Current status (2026-11-24):**

- **Controller.** The 8031 firmware runs and is understood in detail. Its
  scrambler polynomials, synchronous line-side USART and V.25 timing constants
  point to a V.26 ter-class 2400 bit/s duplex echo-cancelling modem.
- **Bit-slice board.** It is very probably the modem's signal processor:
  modulator, demodulator and echo canceller. Its microcode runs under assumed
  field mappings, but the algorithm is not yet identified.
- **Next steps:** [analysis/microcode/PLAN-2.md](analysis/microcode/PLAN-2.md).

The controller ROM **810244E executes unchanged** in a bounded 8031 harness.
With explicitly synthetic serial-shift input, serial status and a retained-RAM
startup model, it initializes both external serial interfaces, runs timer
interrupts and repeatedly enters the main loop. This is **not yet a complete
modem emulator**: neither a telephone-line connection nor the bit-slice signal
processor has been demonstrated.

## Identification from the owner's photographs

The [case marking](photos/PXL_20261123_114938687.jpg) reads **NOKIA DATA MODEM
2400 / 2400**. This establishes the front-panel product designation, not a
more specific unphotographed type/serial number. The
[front panel](photos/PXL_20261123_114949334.jpg) has physical switches and status
indicators; a Hayes-style command interface is not established.

| Board marking | Visible hardware / interpretation | Evidence |
| --- | --- | --- |
| DSU 3555, Nokia 9970067, 1175512 | Transformers and analog circuitry; analog line/interface board | [Front](photos/PXL_20261123_114637263.jpg) / [back](photos/PXL_20261123_114645232.jpg) |
| DSU 3556, Nokia 1177954 | Intel P8031, two AMD P8251A USARTs, EPROM 810244E; controller/interface board | [Front](photos/PXL_20261123_114723348.jpg) / [back](photos/PXL_20261123_114730247.jpg) |
| DSC 3557, Nokia 9970356a, 1177033 | Four MCM93422 SRAMs; socketed 810241 and additional labelled devices 810111/810112 | [Front](photos/PXL_20261123_114811760.jpg) / [back](photos/PXL_20261123_114818924.jpg) |
| DED 3558, Nokia 9970362 B, 1176272 | Digital logic and DAC0830; conversion/timing role inferred | [Front](photos/PXL_20261123_114854803.jpg) / [back](photos/PXL_20261123_114901193.jpg) |
| DSC 2847, Nokia 9996446 C, 1177201 | Two Am2901BDC slices, Signetics N8X02AN sequencer, four MMI PROMs and output latches; microprogrammed datapath | [Front](photos/PXL_20261123_114926601.jpg) / [back](photos/PXL_20261123_114932814.jpg) |

The owner explicitly confirmed **810244E** as the dumped 2764 on DSU 3556.
The full DSC2847 photograph also confirms **position 11 = 810238C**, previously
inferred from a cropped photo. The 512-byte Am27S31DC probably corresponds to
**810241 on DSC3557**, based on the socketed AMD DIP24 photo and acquisition
sequence, but its sticker association has not been confirmed by the owner.
810111/810112 are additional labelled devices; their types and dumpability are
not established. Do not treat the six acquisitions as every programmable device
in the chassis.

All 22 supplied photographs are preserved unchanged. Their source ZIP and
SHA-256 values are in [photos/manifest.json](photos/manifest.json).

## Preserved ROMs and their likely roles

| Image | Size | Interpretation |
| --- | --- | --- |
| [810244E / 2764](controller-810244e/) | 8 KiB | 8031 controller program, physical association owner-confirmed |
| [810237C–810240C](microcode-810237c-810240c/) | 4 × 1 KiB | Candidate parallel microcode lanes for the Am2901 datapath, not an 8051 program |
| [Am27S31DC](am27s31dc-prom/) | 512 B | Lookup/control data; contains an exact signed sine table at its beginning |

The four MMI PROMs and four nearby octal latches suggest **1024 × 32 bits of
control store**. The two 4-bit Am2901 slices suggest an 8-bit datapath. These are
architecture inferences, not a traced netlist. PROM output order, address wiring,
sequencer command/branch wiring and ALU control fields must be established before a
credible bit-slice emulator can execute them. [PROM lane CSV](analysis/results/prom-lanes.csv)
keeps physical chip columns without claiming a 32-bit instruction order.
The [AMD Am2901B/C datasheet](https://pccomponents.com/datasheets/ADVAN-AM2901BDMB.pdf)
provides the slice semantics, but cannot supply Nokia's board-specific wiring.

A subsequent [bit-slice execution experiment](analysis/microcode/README.md)
identified position 9 as a **Signetics N8X02AN**, built functional Am2901/8X02
models, and passed 11 component tests. An explicitly unverified wiring map
executes two PROM words before encountering an unknown stack return. This is
not faithful Nokia microcode execution; a pin-tracing worksheet records what
is needed to establish the actual control fields.

The [photo-only board reconstruction](analysis/microcode/board/README.md) now
provides annotated views, a 30-position inventory, four-state event simulation,
and separate Am2901 slices. Its 18 additional tests pass, including a synthetic
control-store integration run. No complete executable Nokia pin-to-pin nets
have been recovered: the strict real-board startup stops before its first
cycle rather than using the earlier guessed instruction mapping.

The first 16 Am27S31 bytes are **exactly**
`round(127 × sin(2πn/16))`, interpreted as signed bytes. This strengthens the
lookup-table interpretation; sample clock and actual modem carrier frequency
are still unknown. A later [dispatch study](analysis/microcode/assumed/ROM-DISPATCH.md)
also identifies an exact 65-sample quarter sine at 100–140 and ROM byte ranges
matching candidate microcode branch/call targets. The inter-board address path
remains a hypothesis. [Plot](analysis/results/sine-table.svg) ·
[all 512 values](analysis/results/am27s31.csv).

## Controller execution and recovered interfaces

Reset jumps from `0000` to `1EAA`. At `1EB8`, the firmware compares internal
RAM locations 00–5F with their addresses. On the first mismatch it stores the
address there and loops at `1EC4`. Zero-filled emulated RAM therefore **does not
boot past this check**. Retaining RAM across 95 synthetic resets lets the ROM
itself initialize the required pattern; the 96th start proceeds. Alternatively,
starting with that explicit address pattern also proceeds. No ROM byte or PC
is patched. This shows a possible reset-assisted startup mechanism, **not proof
that the physical modem implements this reset sequence**. Actual reset/watchdog
wiring or an oscilloscope trace is needed to settle it.

Afterwards the program clears RAM, sets SP=6F, initializes hardware and enters:

| Address | Observed purpose |
| --- | --- |
| 1DD0 | Initialization; USART setup and a lengthy output-sequencing loop |
| 07D7 / vector 001B | Timer 1 handler; reloads FC21 and decrements software counters |
| 006E–012C | Fourth output-byte builder: five-bit state code plus three flags |
| 012F–0263 | Third output-byte builder with RAM 49/4A/65 counter updates |
| 0266–0430 | First two output-byte builders, retaining event-qualified bits 30.2 and 31.4 |
| 0620 | Stateful decoding of normalized RAM 2A–2F input bits into mode and selector flags |
| 1760, 1790 | Countdown-weighted event accumulation and qualification into outgoing RAM 30.2/31.4 |
| 0800 | Mode-0 serial input: one discarded byte, then six bytes into RAM 2A–2F; P1.0/P1.1 handshake |
| 0899 | Mode-0 serial output from RAM 30–33, with XOR masks 00/03/00/F8, then P1.2 latch pulse |
| 053E / 05A3 | Verified 23-bit scrambler / descrambler; selectable delays (5,23) or (18,23), LSB-first |
| 1D05 | External USART reset/mode/command sequence |
| 1ED6 | Main polling/control loop, calls 0800, 0620, 1000, 1790, 006E, 0899, 08E9 |
| MOVX 0001 / 0005 | First USART data / control-status, inferred from reset sequence and status-bit use |
| MOVX 0002 / 0006 | Second USART data / control-status, same evidence |
| MOVX 8004 | Repeated hardware read selected with P2.7; purpose unconfirmed |

A [local interface study](analysis/microcode/assumed/CONTROLLER-INTERFACE.md)
verifies byte order, XOR masks, input changed-state detection and P1 handshake
ordering with 4,362 varying-byte and completion-delay fixtures. In particular,
P1.2 is not pulsed until the fourth transmitted byte completes. These tests
do not identify the physical destination of the serial chains.

The [external-read study](analysis/microcode/assumed/CONTROLLER-READ.md) finds
that the three observed callers of 08DD overwrite the byte returned from the
8004 read before using it. The main loop still executes that bus cycle on each
iteration; an external side effect remains possible and unidentified.

For example, synthetic zero shift inputs cause control writes
`80 00 40 6E 35` to 0006 and `80 00 40 CC FF 15` to 0005.
These match an 8251-style initialization pattern. The early mode-0 output frame
is `00 02 AC FC`. Bit-to-switch/LED mappings remain untraced: those bytes are
captured outputs, not a claim about physical indicators.
[Intel's 8251A handbook](https://mark-ogden.uk/files/intel/publications/9800676B%20Peripheral%20Design%20Handbook-Feb79.pdf)
documents the status and mode/command semantics used to interpret these accesses.

## Reproduce the execution

From the repository root, using Python 3 and a C compiler:

```sh
python3 nokia/data-modem-2400-2400/analysis/run.py --out /tmp/nokia2400-results
python3 nokia/data-modem-2400-2400/analysis/analyze_proms.py
```

The second command uses optional `matplotlib` to regenerate the SVG; CSV/JSON
analysis needs only the standard library. The first command checks the exact
ROM SHA-256 and builds a harness against the repository's MIT-licensed
[emu8051 core](../../unknown/satellite-mac304-m27c2001/analysis/emulation/emu8051/).
Its existing provenance and fixes are recorded in
[UPSTREAM.json](../../unknown/satellite-mac304-m27c2001/analysis/emulation/UPSTREAM.json)
and [core-fixes.patch](../../unknown/satellite-mac304-m27c2001/analysis/emulation/core-fixes.patch).
No core files were changed for this investigation. The harness adds the P2 high
address byte to MOVX @Ri callbacks, which this core otherwise reports as low-byte
addresses, and supplies mode-0 completion events absent from its UART model.

### Explicit simulation assumptions

- 128-byte 8031 internal RAM; ROM loaded at 0000–1FFF, FF elsewhere. Execution
  outside the dumped ROM terminates with an error.
- Cold RAM starts zero. `WATCHDOG=1` retains RAM and resets CPU only when waiting
  at 1EC4, on 2,000-cycle boundaries. This is a diagnostic experiment, not a
  measured watchdog model. `PRESEED=1` separately seeds addresses 00–5F.
- `SHIFT=0`, `255` or `7` supplies every mode-0 received byte with that chosen
  value. Receive-ready occurs every eight machine cycles when enabled; writes
  to SBUF complete after eight cycles. No switch wiring or physical serial
  waveforms are modeled.
- External reads return 05 (for an 8251: TxRDY and TxEMPTY set, RxRDY clear).
  This applies to unknown ports too and is intentionally a coarse stub, not
  a complete 8251 model. External writes are observed and retained for reporting.
- P1/P3 external inputs are high, masked by their output latches. Timer 1 runs
  in the CPU core. No analog path, remote modem, receive traffic or bit-slice
  interaction is simulated. Cycle totals are not claims of wall-clock accuracy.

## Results and limitations

[Machine-readable results](analysis/results/SUMMARY.json) and
[bounded traces](analysis/results/) are checked in. Traces include every first
executed instruction address, limited early I/O events, and aggregate counts in
the summary. A linear disassembly is included for navigation; data tables in it
must not be mistaken for instructions.

| Scenario | Unique instruction starts | Main-loop entries | Timer-1 entries |
| --- | ---: | ---: | ---: |
| Cold, no synthetic reset | 14 | 0 | 0 |
| Retained resets, no shift input | 69 | 0 | 1,803 |
| Shift input 00, 20M cycles | 1,035 | 11,492 | 19,740 |
| Shift input FF, 20M cycles | 848 | 13,243 | 19,740 |
| Shift input 07, 20M cycles | 869 | 12,735 | 19,734 |
| Preseeded RAM, shift 00, 20M cycles | 1,032 | 11,688 | 19,929 |

All six scenarios passed their checks with no CPU-core exceptions. Main-loop
and interrupt execution demonstrate that meaningful firmware paths run, not
that all code is correct or that the modem can establish a connection.

The next fidelity improvements require tracing the 8031 reset network and
mode-0 shift-register chains, decoding the DSC2847 control-store wiring, and
identifying the additional labelled devices on DSC3557. Front/back photos are
useful evidence but do not uniquely reveal every net or programmable-device
function. A full telephone-line demonstration remains outstanding.

The [input-decoder study](analysis/microcode/assumed/CONTROLLER-DECODE.md)
checks routine 0620 against a reference over 10,144 cases, covering every
instruction in the routine. Physical switch/status labels remain unidentified.
