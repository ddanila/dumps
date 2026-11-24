# Nokia Data Modem 2400/2400: hardware and firmware investigation

## At a glance

| Folder | Contents |
| --- | --- |
| [controller-810244e/](controller-810244e/) | 8 KiB 2764 from DSU 3556: the 8031 controller program |
| [microcode-810237c-810240c/](microcode-810237c-810240c/) | 4 × 1 KiB MMI 6381 PROMs from DSC 2847: the Am2901/8X02 control store |
| [am27s31dc-prom/](am27s31dc-prom/) | 512 B Am27S31DC: sine and lookup tables, probably 810241 on DSC 3557 |
| [photos/](photos/) | All 22 owner photographs, unchanged, with hashes |
| [analysis/](analysis/) | 8031 harness and controller studies; [microcode/](analysis/microcode/) holds the bit-slice work |

## What the modem is

A **V.26 ter-class 2400 bit/s full-duplex modem**, most likely (about 75%).
V.26 ter uses an 1800 Hz carrier, 1200 baud 4-phase DPSK and echo
cancellation. The evidence, all from the controller side, is set out in
[PLAN-2](analysis/microcode/PLAN-2.md):

- **Scrambler.** The 8031 firmware's scrambler pair exactly matches V.26 ter's
  call and answer polynomials (1+x⁻¹⁸+x⁻²³ and 1+x⁻⁵+x⁻²³).
- **USARTs.** One 8251A is programmed for synchronous mode and carries the
  scrambled line bitstream. The other is the switch-selectable DTE port
  (start-stop or synchronous).
- **Handshake timing.** The controller reloads countdowns of 1805, 2605,
  250 and 2000 ticks. Its tick is approximately 1 ms, so these durations
  resemble V.25/V.26 ter handshake windows; the state roles remain hypotheses.
- **Dates.** The boards are date-coded 1984, the year V.26 ter was approved.

The **8031 controller** handles the DTE port, scrambling, the handshake and
the front panel. Its firmware runs unchanged in an emulator and is understood
routine by routine ([controller studies](analysis/controller/)).

The **DSC 2847 bit-slice board** (two Am2901s and an 8X02 sequencer) is very
probably the signal processor: modulator, demodulator and echo canceller. Its
microcode runs under assumed field mappings, but the algorithm is not yet
identified; see [analysis/microcode/](analysis/microcode/). A telephone-line
connection has not been demonstrated.

## Boards

The [case marking](photos/PXL_20261123_114938687.jpg) reads **NOKIA DATA MODEM
2400 / 2400**. The [front panel](photos/PXL_20261123_114949334.jpg) has
switches and status LEDs; there is no evidence of a Hayes-style command set.

| Board | Hardware and role | Photos |
| --- | --- | --- |
| DSU 3555, Nokia 9970067, 1175512 | Transformers and analog circuitry: line interface | [Front](photos/PXL_20261123_114637263.jpg) / [back](photos/PXL_20261123_114645232.jpg) |
| DSU 3556, Nokia 1177954 | Intel P8031, two AMD P8251A USARTs, EPROM 810244E, 11.9808 MHz oscillator: controller | [Front](photos/PXL_20261123_114723348.jpg) / [back](photos/PXL_20261123_114730247.jpg) |
| DSC 3557, Nokia 9970356a, 1177033 | Four MCM93422 SRAMs (256 × 4); socketed 810241 and labelled devices 810111/810112: probably data memory for the signal processor | [Front](photos/PXL_20261123_114811760.jpg) / [back](photos/PXL_20261123_114818924.jpg) |
| DED 3558, Nokia 9970362 B, 1176272 | Digital logic and a DAC0830: conversion and timing | [Front](photos/PXL_20261123_114854803.jpg) / [back](photos/PXL_20261123_114901193.jpg) |
| DSC 2847, Nokia 9996446 C, 1177201 | Two Am2901BDC slices, N8X02AN sequencer, four MMI 6381 PROMs, output latches, 14.400 MHz oscillator: bit-slice signal processor | [Front](photos/PXL_20261123_114926601.jpg) / [back](photos/PXL_20261123_114932814.jpg) |

- **Confirmed chips.** The owner confirmed **810244E** as the dumped 2764 on
  DSU 3556. The full DSC 2847 photo confirms position 11 = **810238C**.
- **Am27S31DC.** The 512-byte Am27S31DC is probably **810241 on DSC 3557**,
  but that association is unconfirmed.
- **Not yet dumped.** 810111 and 810112 have not been dumped, and their types
  are unknown. They may matter for the signal-processing picture.

All 22 photographs are preserved unchanged; their hashes are in
[photos/manifest.json](photos/manifest.json).

## The lookup PROM

The first 16 Am27S31 bytes are **exactly** `round(127 × sin(2πn/16))` as
signed bytes, followed by four wrap-around entries, so a cosine can be read
4 entries ahead. Bytes 100–140 hold an exact 65-sample quarter sine. Other
regions hold smooth curves that look like filter or gain tables.
[Plot](analysis/results/sine-table.svg) · [all 512 values](analysis/results/am27s31.csv).

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
| MOVX 0001 / 0005 | Line-side 8251 data / control (synchronous mode, external sync; carries scrambled data) |
| MOVX 0002 / 0006 | DTE-side 8251 data / control (start-stop or synchronous, chosen by switches) |
| MOVX 8004 | Repeated hardware read selected with P2.7; purpose unconfirmed |

A [local interface study](analysis/controller/INTERFACE.md)
verifies byte order, XOR masks, input changed-state detection and P1 handshake
ordering with 4,362 varying-byte and completion-delay fixtures. In particular,
P1.2 is not pulsed until the fourth transmitted byte completes. These tests
do not identify the physical destination of the serial chains.

The [external-read study](analysis/controller/READ.md) finds
that the three observed callers of 08DD overwrite the byte returned from the
8004 read before using it. The main loop still executes that bus cycle on each
iteration; an external side effect remains possible and unidentified.

For example, synthetic zero shift inputs cause control writes
`80 00 40 6E 35` to 0006 and `80 00 40 CC FF 15` to 0005.
These match an 8251-style initialization pattern. Decoded, mode `CC` with
sync character `FF` is synchronous, 8-bit, external sync detect, and `6E` is
asynchronous ×16, 8 data bits, no parity. The early mode-0 output frame
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

The [input-decoder study](analysis/controller/DECODE.md)
checks routine 0620 against a reference over 10,144 cases, covering every
instruction in the routine. Physical switch/status labels remain unidentified.
