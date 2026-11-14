# 7200 MEGACPU 26300-85-V firmware investigation

Analysis date: 2026-11-14. Input: the eight verified 64 KiB acquisitions in the
parent directory. Chip 7 / U605 is absent. No replacement dump has been recovered.
The original acquisition files have not been changed.

**Result:** original firmware instructions run from reset, through the early
self-tests, into application initialization and an event scheduler.
With explicitly synthetic peripheral behavior, the program sends initialization
bytes to a serial device, samples a memory-mapped converter, formats diagnostic
messages, and enters its terminal fault handler. This is **not a working emulator
of an entire ventilator or a successful normal boot**. It does not demonstrate
that any ventilation-control algorithm works. No physical board is driven.

The text inventory and the execution evidence below establish considerably more
than a `strings` listing, but do not constitute a complete decompilation. In
particular, the missing bank's contents, every text consumer, option activation,
closed-loop behavior, graphics protocol and normal UI navigation remain unresolved.

## Files and reproduction

- [Searchable text catalog](catalog/strings.html): open locally in a browser.
- [Text CSV](catalog/strings.csv), [JSON](catalog/strings.json): all maximal printable
  runs of at least four characters, including machine-code coincidences.
- [Decoded option records](catalog/option-menu.json): fixed-width menu entries.
- [Executed disassembly](catalog/executed.asm): instructions observed in strict/mock/explore/analog/format-ab runs; excludes the two divergent negative experiments.
- Each `results/NAME/` contains registers, stop reason, explicit intervention
  events, last 2,000 instructions, first 10,000 I/O events, coverage, text/data
  read sites, observed call edges, instruction decoding and captured serial bytes.
  Addresses in JSON are decimal unless represented by a hex string. `instructions.json`
  retains CS:IP; `calls.json` records actual observed call destinations, including
  indirect calls. A first-seen CS alias is used for each physical instruction.
- [Harness](run.py), [catalog generator](catalog.py), [verification](verify.py).

From this directory:

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python run.py --output results/strict
.venv/bin/python run.py --mock --output results/mock
.venv/bin/python run.py --mock --explore --output results/explore
.venv/bin/python run.py --mock --explore --analog --steps 2000000 --output results/analog
.venv/bin/python run.py --mock --explore --fault-code 0xab --output results/format-ab
.venv/bin/python run.py --mock --explore --native-far-return --output results/native-return
.venv/bin/python run.py --mock --explore --analog --continue-faults --output results/continued
.venv/bin/python catalog.py
.venv/bin/python verify.py
```

Python 3, Unicorn 2.1.4, Capstone 5.0.7. Runtime memory snapshots are generated but
ignored by Git; the raw ROMs plus scripts reproduce them. `strict` means *no
optional hardware interventions*, not an accurate hardware model: even this
profile uses ordinary RAM, last-written-value I/O latches and the segmented-return
compatibility implementation. Execution is instruction-count bounded, not cycle timed.

## CPU, memory and program organization

The firmware is 16-bit segmented x86. Reset contains `EA 00 00 C0 FF`, jumping to
`FFC0:0000` (physical `FFC00`). The reset routine programs the 80186/80188 integrated
chip-select and timer registers at `FFA0`–`FFA8`, `FF56`, `FF58`–`FF66`, then jumps to
`FE00:0035`. This strongly supports the proposed 80188-family identification; it
does not identify the physical package's exact CMOS suffix or clock rate.

The manufacturer service manual describes the 80188 CPU board and 512 KiB of
shared program EPROM. It also identifies the display-controller sensor ROMs as
calibration tables, and its serial controllers as interfaces for external devices.
See [Puritan Bennett 7200 Service Manual, 066317 Rev. A, March 2004, section 2](https://pdfcoffee.com/ventilador-7200-manual-servicio-pdf-free.html).
That manual is later than this firmware and is corroborating architecture evidence,
not proof of the exact configuration of these boards.

The execution model uses this mapping:

| Chip | Physical address | Interpretation supported by this investigation |
|---|---|---|
| 0 | F0000–FFFFF | Local startup/POST; lower 32 KiB is CC padding |
| 1 | 00000–0FFFF | Interrupt vectors, tables, English UI text, some code |
| 2 | 10000–1FFFF | UI/graphics text and application material |
| 3 | 20000–2FFFF | Application routines, converter access, utilities |
| 4 | 30000–3FFFF | Application routines, fault handler, report material |
| 5 | 40000–4FFFF | Application/control routines |
| 6 | 50000–5FFFF | Application/diagnostic routines and data |
| 7, absent | 60000–6FFFF | Unknown; FF-filled placeholder, never executable |
| 8 | 70000–7FFFF | Runtime/scheduler, interrupt handlers, serial routines |

These are not eight independent programs. Far calls and pointers connect the
banks, and the low-address interrupt vector table already points into chip 8.
For example `INT BA` has vector `7D40:0002`; startup uses the chip-3 function at
`221F:0010`. The proposed consecutive mapping supports actual execution across
banks. A schematic-accurate bus decoder has not been reconstructed.

`80000`–`EFFFF` is permissive zero-initialized RAM in the harness, including
locations that are actually memory-mapped peripherals. The ROM windows are
write-protected during CPU execution. Successful runs do not depend on permitting
writes to program ROM. Stack and data segments include `AFF8`, `AFE0`, `8260`,
`89B0`, `8C42`, and `7FA0`; the latter's used offsets extend into RAM above `80000`.
Sensor calibration ROMs Q1–Q3 are preserved separately, but their actual decode
and corresponding analog plant are not implemented here.

The startup image contains a real additive checksum: sum of chip-0 bytes
`8002`–`FFFF`, modulo 65536, is `FEED`, equal to the stored word at `8000`.
The routine at `FE62C`–`FE665` verifies this before transferring to `F810:059A`.
This check passes without modifying the ROM. It is not a checksum of chip 7.

## What actually executes

| Profile | Outcome | Interpretation |
|---|---|---|
| strict | POST failure at FE012 | Watchdog reset never arrives in a latch-only environment |
| mock | POST failure at FE012 | Early watchdog/timer accommodations pass; later board test still fails |
| explore | Terminal fault loop at 3A39F | Scheduler and serial initialization run; ADC-ready polling times out; message ERR9904 |
| analog | Terminal fault loop at 3A39F | Synthetic completed ADC advances execution; diagnostic path eventually produces ERR9909 |
| format-ab | Terminal fault loop | Change only the fault argument to AB to exercise original message formatting |
| native-return | Write-protection exception | Without the segmented-return compatibility path, this integration diverges |
| continued | Write-protection exception | Returning from a nonreturning diagnostic routine does not establish a valid continuation |

The explore run executes 327,170 instructions at 5,141 distinct addresses;
the ADC run executes 1,245,829 at 7,209 addresses. Across the five principal
profiles the catalog includes 7,381 distinct executed addresses. The text
inventory has 2,856 printable runs, 827 with candidate pointer matches and
77 with an observed data reader. Exact states are in the committed results. Neither main
exploratory path reads or executes `60000`–`6FFFF`. Thus the current stopping
conditions are **not evidence that the missing ROM has been reached**. There is
no justified chip-7 replacement routine to invent from these traces. If execution
enters that range the harness records the state and stops; data reads are logged
and receive the conspicuous FF placeholder. FF is an experiment policy, not a
claim about the absent ROM's content.

A byte-pattern scan for `9A` plus a far address into bank 7 yielded apparent calls
inside instruction operands (`CS:[009A]`, `[BX+089A]`), not real call instructions.
Do not use such matches to claim that a particular missing function was identified.
Likewise the thousands of entries in `missing-pointer-candidates.json` are only
aligned four-byte arithmetic matches, not verified pointers or a call graph.

### All interventions and model limits

1. Unimplemented IN ports return the most recent OUT value, otherwise all ones.
   This is deliberately simple and can produce unrealistic device responses.
2. `--mock`: at `FE439`, restart at the reset vector with RAM retained, simulating
   the watchdog event expected after firmware stores AB at `80DF6`. At `FE601`,
   set `80DF2=2A`, the timer-test completion flag. This is a test-result mock,
   not execution of the timer interrupt handler. For the later low-power polling
   code, C200 returns EF, clearing bit 4. The watchdog/timer/POST transitions are recorded in `events`; continuous
   port and ADC policies are identified by the source/profile.
3. `--explore`: set the board POST loop index at `AFE91` to 15 hex at `F86B4`.
   This bypasses that loop; none of its skipped checks is claimed to pass.
   BD00/BD01/BD10/BD11 return 04 (transmitter-ready policy). At every hundredth
   visit to scheduler idle `7E39D`, inject interrupt 13 hex through the original
   vector table. This is synthetic timer-2 scheduling, not elapsed physical time.
4. `--analog`: reads of `90000` clear busy bits 7 and 6, and return a constant
   0800 converter word at `90001`. All channels receive the same invented sample;
   this is not a physiological or calibrated sensor model.
5. `--fault-code`: overwrite the first fault handler's stack argument for a
   formatter experiment. `--continue-faults` additionally makes the diagnostic
   routine at `53BEE` return as though `RETF 14` had occurred. The latter experiment
   fails later and is retained as negative evidence, not advertised as a fix.
6. RETF/RETF-immediate/IRET are implemented explicitly from the emulated stack.
   Without this path, the instrumented firmware run resumed at an incorrect offset
   after a far return, and later protection checks caught corruption. A minimal
   isolated far-call/return experiment succeeded with native Unicorn, so this has
   **not** been established as a general Unicorn defect. The compatibility path
   and native comparison are part of the experimental limitation. Software
   interrupts push FLAGS/CS/IP and dispatch through the actual vector table.
7. No real interrupt controller, DMA, display controller, keyboard matrix,
   RTC/BBR, pneumatic system or accurate serial protocol endpoint is modeled.
   No MAME 80188-core cross-validation was completed. Unicorn's x86 engine supplies
   the instructions; it is not an 80188 system emulator.

## Proven text-to-code paths

### ADC timeout → ERR9904

At `29A1:0734` (physical `2A144`), code tests bits C0 at the far pointer held at
`CS:0144`. That pointer resolves to `90000`. The associated converter result
pointer at `CS:0140` resolves to `90001`.

After more than 100 unsuccessful polls, `2A15B` pushes argument 4 and `2A15D`
calls `3A15:0030` (physical `3A180`). The fault routine reads its template via
`CS:002C`, pointing at **00000:38B2 / physical 038B2** in chip 1, copies 20 bytes,
and calls the formatter at `2C96:000E`. It writes the resulting display buffer
in reverse character order through another pointer, updates diagnostic state,
and enters a permanent loop that continues feeding the watchdog while writing
C202=00 and C203=08.

The internal buffer at `8C450` contains ` ERR9904 DO NOT USE ` plus trailing control
metadata. This is an actual original-code formatting path, not text printed by
the harness. The `format-ab` run changes the argument and records the result in
`display-fault-buffer.txt`; it produces `ERR99AB`, demonstrating hexadecimal rather than decimal formatting.
The catalog's raw printable run starts earlier than 038B2 because adjoining
records contain no nonprintable delimiter.

### Diagnostic record → ERR9909

The ADC mock gets beyond the first timeout. A later diagnostic enters `53BEE`,
which packages seven stack arguments and time/status fields into a diagnostic
record. Its path eventually pushes 9 at `53E4F` and calls the same fault routine
at `53E51`, giving ` ERR9909 DO NOT USE `. This identifies the terminal message
path, not the real-world service diagnosis of a physical board. Arguments and
caller return addresses are recorded in the `diagnostic failure entry` event.

### Display/serial initialization and runtime

The code at `76558` reads BD11 and waits for bit 2; `76574` sends a byte to BD13.
The explore run captures 29 bytes in `tx-bd13.bin`, beginning
`7F 00 7F 1B 1B 1B 1B 1B 0C`. They are binary/control traffic, not a rendered
screen. The connected endpoint and full command protocol remain unverified.

`7DFBE` invokes `INT BA` as a runtime service; original vector code dispatches it.
The idle/scheduling code around `7E373`–`7E3A9` traverses work structures and waits
on state at DS:0D63. Synthetic timer interrupts release scheduled activity.
This establishes a runtime and event-driven structure, not an identification of
a commercial RTOS or proof of real-time scheduling behavior.

## Features represented in the firmware

These are **present-in-image findings**. An option label does not prove it was
licensed/enabled on this board or that its implementation is intact without chip 7.
Physical addresses below refer to the proposed mapping; chip 1 offsets equal
physical addresses. Full text and neighboring control bytes are in the catalog.

| Area | Evidence / location | What can be concluded |
|---|---|---|
| Power-on and extended tests | chip 0 POST; 02D00–031DD front-panel prompts | CPU/RAM/timer/watchdog startup; quick/total EST, leak, compliance, flow comparison, compressor, nebulizer, front panel, DCI, PSOL and Flow-by tests |
| Operator fault handling | 038B2 template; 3A180 handler | Original code constructs ERR99xx DO NOT USE and enters a terminal state |
| Apnea support | menu 050BD; prompts from 0572E | Volume apnea parameter entry and related settings; also a pressure-control apnea menu |
| Respiratory modes/options | option table 050BD–054BE | Pressure support, pressure control, Flow-by 2.0, auto-PEEP, apnea-related options are represented |
| Patient measurements | menu 0510F, 05280–05324; chip-2 text | Patient data, static/respiratory mechanics, negative inspiratory pressure, vital capacity, peak spontaneous flow, compliance/resistance |
| Graphics and history | 05376, 0539F, 053C8; chip-2 text | Waveforms, trending, freeze/print UI assets exist |
| Communications | 0518A–051DC; baud strings at 0487A | Report setup, communications control, patient data log; host/printer and parity/enable labels |
| Reporting | 05205–05257; chip-4 templates | Chart summary, ventilator status and EST reports; identifiers include PD, AL, AS, VS, ER, BBR, PID, PCV, VSR, EST and OXD/OXA/OXM |
| Pulse oximetry | 0546C–054BE, 04E99 onward | Pulse oximetry, alarm limits, miscellaneous controls, SpO2 text |
| Service/calibration | 03242 onward | Sensor Q1/Q2/Q3 and pressure sensor diagnostics, PSOL current tests, compliance/leak/area-ratio results, BBR and autozero messages |
| Firmware identity | chip-1 strings | 26300-85-V; model names 7200e/7200spe/7200ae; timestamp-like 19951018080000 |

The timestamp resembles 1995-10-18 08:00:00; it has not been independently proven
to be the build time. The displayed option numbers are useful indexes into the
UI, not reconstructed function numbers. The fixed option table has 41-byte records:
36 text bytes followed by five bytes of metadata whose complete semantics are
not decoded. Plain ASCII extraction merges adjacent records and includes control
characters when their numeric values are printable.

## Reading the string references correctly

`pointer_candidates` lists file locations whose four bytes can be interpreted as
an offset:segment pointer to the start of a raw printable run. This intentionally
includes false positives, misses interior pointers, and does not discover computed
indexes. `observed_readers` lists PCs that actually read any byte of that run;
checksumming and block-copy routines are also readers. Neither field alone proves
that text is displayed or that a particular feature is reachable.

The direct fault-handler chain above is verified separately because a template
address, copy, formatter call, resulting RAM text and final output behavior can
all be connected. Most other texts can currently be assigned to an intended UI
or report by their wording/table context, but not to a fully verified execution
path. Do not promote those associations to exact code-level cross references.

## Remaining work

A complete normal boot requires a more faithful model of peripheral completion,
calibration ROM mapping, configuration/BBR and interrupt timing. The negative
continued-fault run shows why simply returning from every diagnostic failure is
not an adequate solution. Next useful work is hardware/schematic mapping and
recovery of chip 7 from a matching 26300-85-V set, followed by instrumented normal
UI navigation and reconstruction of text dispatch tables. More accurate peripheral
models may expose the missing bank; current absence of an access does not prove
that it is unused or safe to omit.
