# PRU_AC six-chip set: identification and reverse engineering

Analysis date: 2026-09-25. All addresses below are hexadecimal unless stated
otherwise. `CPU` means the reconstructed 68HC11 address space; `offset` means
an offset in the named, unmodified physical capture.

## Identification

**This is Motorola 68HC11 executable firmware for a Landis & Gyr UNIGYR
building-services controller. The six-chip PCB is very likely a PAA1-family
program card for a PRU1 process unit.** The firmware identifies itself as
`PRU_AC  4-NOV-1993 14:47:13`. The likely application is air-conditioning
plus associated building controls. It contains a proprietary function-block
runtime, scheduler, mathematical routines, startup diagnostics and a serial
service monitor.

The exact MCU suffix, PCB revision, PAA1 option/version and PRU1.32 versus
PRU1.64 are **not established**. A1/A8 and E1/E9-class HC11 parts with internal
ROM disabled fit the recovered hardware initialization. No package marking
or board photograph was supplied for this identification.

| Finding | Confidence and basis |
|---|---|
| 68HC11 instruction set | Very high: reset path, three prefix pages, indexed X/Y operations, matching peripheral register setup and vectors |
| Expanded external-memory operation | Very high: fixed external ROM, thirteen software-selected code banks, RAM and external I/O |
| Landis & Gyr PRU / UNIGYR | Very high: manufacturer and product strings plus manufacturer documentation |
| PAA1 program-card family, used with PRU1 | Strong inference: exact 256 KiB EPROM + 32 KiB EEPROM capacity and matching application family |
| PAA1.2A or PAA1.3A | Plausible candidates, not a unique identification; both documented with 32 KiB configuration memory |
| Estonian-language installation with Finnish library text | Strong language evidence; geography and exact premises remain unknown |
| All six captures fully valid | Not established: chip 2 aliases/repeats every 128 bytes; only chip 5 was physically read twice |

The [PAA1 manufacturer datasheet, CM2N8261E, January 1999](https://plone.unige.ch/EULER/technic/Composants/CLIMATISATION/CLIMATISATION_PRIMAIRE_CORALIE/archives-clim-unigyr-1999/Documentation_Elements_Controle/Unigyr_Program_Cards_PAA1.pdf)
links these cards to PRU1.32/PRU1.64. Its type table lists both AC candidates,
and its memory diagram specifies 256 KiB EPROM firmware and 16/32 KiB EEPROM
configuration. It also describes configuration using UNIGYR Design. This is
later documentation of the family, not proof that the 1993 image belongs to
a particular 1999 ordering code. The
[manufacturer service manual CM2B8205E](https://files.elektroda.pl/388561%2Cb8205e.html)
provides additional PRU application-family context.

## What the six chips contain

| Chip | Device / capacity | Interpretation | Capture status |
|---|---|---|---|
| 1 | 28C64 / 8 KiB | Structured binary configuration or persistent state; precise record schema unknown | One read; 162 byte values, no ASCII strings of length 5 |
| 2 | 28C64 / 8 KiB | One structured 128-byte record repeated 64 times | One read; address validity unresolved |
| 3 | 28C64 / 8 KiB | Binary records followed by application labels and parameter descriptions | One read; 64 distinct 128-byte pages |
| 4 | 28C64 / 8 KiB | Related application text, unused space and apparent address-test markers | One read; 41 distinct 128-byte pages |
| 5 | M27C1001 / 128 KiB | Fixed firmware, six code banks, additional small data area | Two identical reads using different address-shifting implementations |
| 6 | M27C1001 / 128 KiB | Seven further code banks and a zero-filled final 16 KiB | One read; firmware checksum agrees with chip 5 |

The images are eight-bit byte streams. Alternating chips 5 and 6 as even/odd
halves of a 16-bit bus is unnecessary and destroys the coherent HC11 code.
Chip numbering records physical provenance, not a proven linear address order
for the four EEPROMs.

### EEPROM text and records

Chip 3's first identifying ASCII text is at offset `0009c0`:
`SJ.SM4:PULSSI_LASKURI`. Other strings include `AJAPROGRAMM`, `AUTOMAATIKA`,
`Reklaamvalgustus`, `Sisevalgustus`, `TAGAHOOV`, `TREPIKODA` and `Tolmueraldus`.
These refer to time programs, automation, advertising/interior lighting,
a rear yard, stairwell and dust extraction. Finnish pulse-counter and alarm
parameter labels appear alongside the Estonian application labels.

CP850 explains several non-ASCII words much better than Latin-1:
chip 3 `001fd0` and chip 4 `000010` give `TULEKAHJU ÜLDAVARII`; chip 4
`000055` gives `Mõõtesuurus (Lux)` and `000068` gives
`Seadeväärtus (0...1000 Lux)`. Bytes `99`, `9a`, `84` and `e4` correspond
to Ö, Ü, ä and õ under that encoding. CP850 is therefore a useful working
interpretation, not a proven universal encoding for every binary field.
The [encoding candidates](text-encoding-candidates.json) retain raw hex,
CP850 and Latin-1 forms, so this interpretation is reversible.

Chips 3 and 4 are related but are not simply one uninterrupted string blob:

| Chip 3 offset | Chip 4 offset | Identical contiguous bytes |
|---|---|---:|
| `0009bf` | `0002c3` | 1289 |
| `001481` | `0007cd` | 1575 |

This could reflect duplicated function-block definitions, saved configurations
or allocation history. The capture does not establish which configuration is
active. Repeated labels alone are not evidence that the reader duplicated a
chip: the long blocks occur at different offsets and the rest of each image
differs. Both images start with binary fields rather than a naked continuation
of a text string. Do not concatenate and claim a recovered runnable project.

Chip 4 has `aa` at `001fff` and `55` at `001fff - 2^k` for k = 0 through 11;
the other bytes from `001700` onward are `ff`. That precise power-of-two
spacing resembles a stored address-line test pattern. Its origin has not been
traced to a firmware routine, so it is an inference, not proof of a successful
self-test. It is useful positive evidence that this capture distinguishes
addresses well beyond the 128-byte boundary that is problematic on chip 2.

Chip 2's repeated record contains plausible sequential identifiers such as
`03 40`, `03 41` through `03 49`, and `01 5b` onward. It is structured data,
not the programmer-output echo pattern seen in earlier, unrelated captures.
However, all address bits A7–A12 select identical data in this image. Actual
stored repetition, a device fault and a contact/address-selection problem
cannot be distinguished offline. Other chips read with the same setup do not
share this aliasing. No bytes were repaired or invented, and this analysis
performed no additional hardware reads.

## CPU identification and architecture survey

The decisive evidence is the correspondence between code and hardware, not
how many arbitrary bytes a disassembler accepts.

Chip 5 offset `003ffe` contains the big-endian reset vector `df5d`. Mapping
its first 16 KiB at CPU `c000` yields:

```asm
df5d: 0f          sei
df5e: 8e 38 00    lds #$3800
df61: bd e0 a6    jsr $e0a6
...
e0a6: 86 a0       ldaa #$a0
e0a8: b7 10 3d    staa $103d   ; HC11 INIT register
...
e0b5: 96 3f       ldaa $003f   ; relocated CONFIG
e0b7: 81 0d       cmpa #$0d
```

This relocates the register block to `0000` and internal RAM to `a000`.
The exact CONFIG comparison expects internal ROM disabled, EEPROM enabled
and COP watchdog disabled on A/E-compatible parts. The RAM test at `e1ec`
tests `0120–5fff` with selector `0f`, then `a000–b5ff` and `b800–bfff`,
skipping the 512-byte `b600–b7ff` EEPROM area. The serial initialization at
`e47a` uses HC11 SCI offsets `2b–2f`; transmit polling and data writes fit
the same register map. These observations agree with the
[Motorola HC11 reference manual](https://www.nxp.com/docs/en/reference-manual/M68HC11RM.pdf)
and [E-series programming guide](https://www.nxp.com/docs/en/reference-manual/M68HC11ERG.pdf).

All 21 vectors from `ffd6` through `fffe` point into the fixed ROM. The SCI
vector points to `e012`, IRQ to `e557`, illegal-opcode vector to `e06e`,
and reset to `df5d`. Full values are in [results.json](results.json).

Chip 6 begins with `PSHX; ABX; STX 13,X; LDY 11,X; LDY 11,Y; LDY 8,Y`.
Branches join on coherent instruction boundaries, pointer accesses retain
meaningful X/Y roles, and subsequent calls use the correct bank-restoring
stub. The HC11 `18`, `1a` and `cd` prefix pages recur consistently in
startup, scheduling and the banked application code.

The [comparison artifact](cpu-comparison.txt) contains actual bounded decodes
under **34 MAME architectures**. These are representative relevant families,
not a claim to test every part number ever manufactured. They cover the
following alternatives:

| Family / tested decoders | Assessment of these bytes |
|---|---|
| 6800/6801/6803, HD6301/HD63701 | Closest superficial resemblance, but do not implement the required HC11 X/Y prefix semantics; reject as the native ISA |
| 6805/68HC05, 6809/HD6309 | Different encoding/register model; fail the same startup and pointer-operation interpretation |
| 8051, Siemens SAB80515; MCS-48/8035/8048 | Many bytes decode, but no consistent reset/vector, peripheral-map or bank-call explanation |
| 8080/8085 via i8085, Z80/Z180, Z8 | Dense encodings accept data readily; they do not explain the positive HC11 fingerprints |
| 6502/65C02 | Different opcodes, vectors and endian conventions; no matching startup interpretation |
| 8086/80186 via x86_16, MCS-96/196 | Different instruction/control-flow models; no supporting reset or peripheral evidence |
| Hitachi H8/H8H; Toshiba TLCS-90/870/900 | Alternative industrial MCU candidates; bounded decodes do not reproduce the coherent HC11 semantics |
| NEC uPD7810/78K0, TI TMS7000, Mitsubishi M37710 | Same negative result against the identified reset and register operations |
| Motorola 68000/68302 via m68000; CPU16 | Neither the byte stream nor bank layout supports these wider Motorola alternatives |
| PDP-11/T11 | Included as an additional period industrial/USSR-relevant architecture; no positive match |

This also rules out an 8080/Z80/8051/8048-compatible Soviet implementation as
the processor executing these EPROMs. The presence of Estonian labels does
not imply a Soviet CPU. A peripheral elsewhere in the original controller
could of course use another ISA; these six chips do not identify every chip
in the complete system. No specifically identified compiler, source language
or commercial RTOS name has been recovered.

### Which 68HC11 variant?

| Candidate | Evidence / limitation |
|---|---|
| MC68HC11A1, A8 with ROM disabled | Strong fit: CONFIG `0d`, INIT and the 512-byte EEPROM hole; A1 is a natural external-ROM candidate |
| MC68HC11E1, E9/711E9 with internal ROM disabled | Also strong fits; the observed accesses do not distinguish their larger internal RAM or masked versus EPROM variants |
| Earlier B-family equivalents | Not uniquely excluded solely by the core opcodes; no positive board evidence selects them |
| A0/E0, D3/711D3 | Poor match to the required enabled EEPROM and the observed memory arrangement; do not infer these from the ISA alone |
| 68HC811E2 / 2 KiB EEPROM derivatives | EEPROM size and mapping differ from the observed 512-byte hole; not the leading candidates |
| 68HC11F1 | Its CONFIG has different mapping fields and fixed bits, including bit 1 reading as one; an exact `0d` check is incompatible with the documented normal register behavior |
| 68HC11K family | CONFIG includes a fixed high bit, and its native bank register has different semantics; not supported by this initialization |

For derivative distinctions see the
[E-family datasheet](https://www.nxp.com/docs/en/data-sheet/M68HC11E.pdf),
[F1 datasheet, CONFIG section](https://www.nxp.com/docs/en/data-sheet/MC68HC11F1.pdf)
and [K-family datasheet, CONFIG and memory expansion sections](https://www.nxp.com/docs/en/data-sheet/M68HC11K.pdf).
In particular, address `0058` alone must not be mistaken for evidence of a
K-family MCU: K's MM1CR ignores bit 0, whereas this program selects distinct
banks with consecutive byte values. An external selector on an A/E-class
system explains the behavior better. Exact package identification remains
necessary to select a hardware-faithful MCU model.

## Reconstructed ROM organization

One fixed 16 KiB window at CPU `c000–ffff` holds startup, vectors, runtime,
math and bank-switching support. Thirteen 16 KiB banks execute at
`4000–7fff`. Firmware writes the selector to `0058` and maintains a shadow
at RAM `37be`.

| Selector | Chip | Physical offset | Caller-bank restore stub |
|---:|---:|---|---|
| fixed | 5 | `000000` | — |
| 0 | 5 | `004000` | `f408` |
| 1 | 5 | `008000` | `f423` |
| 2 | 5 | `00c000` | `f460` |
| 3 | 5 | `010000` | `f47d` |
| 4 | 5 | `014000` | `f49a` |
| 5 | 5 | `018000` | `f4b7` |
| 6 | 6 | `000000` | `f4d4` |
| 7 | 6 | `004000` | `f4f1` |
| 8 | 6 | `008000` | `f50e` |
| 9 | 6 | `00c000` | `f52b` |
| 10 | 6 | `010000` | `f548` |
| 11 | 6 | `014000` | `f565` |
| 12 | 6 | `018000` | `f582` |

For example, bank 1 has 94 raw `JSR f423` occurrences, bank 2 has 103
`JSR f460`, and bank 6 has 82 `JSR f4d4`. None of those banks contains raw
calls to a different listed restore stub. These are byte-pattern counts,
not an assertion that every occurrence is reachable code. Banks 1–12 each
agree with their own restore selector. Bank 0 has no such direct calls;
its assignment is supported less directly by the remaining layout and
selector table, and is therefore the least directly evidenced row.

Stub `f423` selects the destination bank from A, calls through Y, then restores
selector 1 before returning. A table at `dbdc` contains thirteen corresponding
return-site addresses. This explains why naïve linear disassembly of the
whole 128 KiB files produces impossible addresses and apparent corruption.
It does not establish the physical logic equations or EEPROM bank wiring.

Chip 5's last 16 KiB is **not entirely padding**: offset `01c000–01c606`
contains structured data (718 nonzero bytes), followed by zeros through EOF.
Its mapping/purpose is unresolved; possible initialization/configuration data
must not be silently discarded. Chip 6's last 16 KiB is entirely zero.

### Firmware checksum: passes

The routine at CPU `e268–e299` implements:

```text
A = sum(fixed ROM c000..ffaf)
  + sum(fixed ROM ffc8..ffff)
  + sum(each of banks 0..12, addresses 4000..7fff)
expected = (~A) & 0xff
compare expected with ROM byte ffbf
```

Reproduction gives **`c9`, equal to chip 5 offset `003fbf`**. It covers
229352 bytes in the reconstructed fixed and banked ROM regions. This is
substantive evidence that the two EPROMs belong together and that the read
contents and recovered checksum algorithm are plausible.

It is only an eight-bit additive checksum. It cannot prove bank order,
exclude compensating errors, or validate the four EEPROM images. The hole
`ffb0–ffc7` is skipped; nearby code accesses external I/O in that region.
The entire last 16 KiB of each EPROM is also outside this checksum.
The original files, including those areas, are preserved unchanged.

## Runtime, diagnostics and implications for emulation

The fixed-ROM routine at `dc42` masks interrupts and saves registers for
context switching. Initialization at `df64` constructs state using ROM tables;
strings at chip 5 `001391` include cycle-time/process and local-variable
diagnostics. Arithmetic-error strings at `00141d` mention square root,
logarithm and exponential operations. This fits a scheduled function-block
controller with a substantial runtime and mathematical library.

Some undefined opcodes are deliberate traps, not evidence against HC11.
For example, bank 6 CPU `4052` subtracts `10`, `4054` branches around byte
`51` when the range check succeeds, and `4056` traps otherwise. The illegal
vector leads via `e06e/e06b` to `e5ab`, which examines the stacked PC and
faulting opcode. Other guarded trap bytes and table/data bytes make a
whole-ROM “percentage legal instructions” score actively misleading.

The monitor near `e5d5` dispatches command bytes `R W S K P D B I L V`.
The nearby code includes memory-access operations and a jump back to reset.
The SCI helper at `e486` polls serial status and handles `13`/`11` flow-control
bytes. These are useful entry points for a future emulator; this analysis
has not exercised the monitor or decoded its complete wire protocol.

A credible emulator would need an A/E-compatible HC11 core, the fixed/banked
ROM map, register relocation, RAM, selector and external I/O behavior, timer
and serial devices, and a verified mapping for the four EEPROMs. The missing
on-chip EEPROM/CONFIG and possibly other base-unit firmware/state are not
contained in these six external chips. Oscillator frequency, board wiring
and peripheral identities are not established by the current evidence.
**No full-system boot or successful application execution is claimed.**

The current useful result is a defensible hardware-family identification,
recoverable code banks and vectors, a passing original ROM checksum, and a
record of the installation data with its unresolved capture defect. A future
MAME implementation can build on this without guessing that the six files
alone represent the entire controller.

## Reproduce

From the repository root, with Python 3:

```sh
python3 landis-gyr/pru-ac-20260924/analysis/analyze.py
```

To regenerate the disassembly artifacts as well:

```sh
python3 landis-gyr/pru-ac-20260924/analysis/analyze.py --unidasm /path/to/unidasm
```

The checked artifacts use MAME tools package `0.285+dfsg1-1`; the executable
SHA-256 and decoder names are in [decoder.json](decoder.json). See the
[primary MAME decoder source](https://github.com/mamedev/mame/blob/master/src/devices/cpu/mc68hc11/hc11dasm.cpp)
for decoder implementation. Tool syntax omits `#` on immediate operands in
the raw [HC11 excerpts](hc11-excerpts.asm); the annotated snippet above adds
it for readability. Truncated final instructions are omitted rather than
publishing the zero operands unidasm supplies beyond EOF.

Generated files include hashes, entropy and address-bit comparisons,
vector values, bank/stub counts, the original checksum calculation,
ASCII strings, encoding candidates and shared configuration blocks. A
single-bit mutation in a temporary in-memory copy checks checksum sensitivity;
it does not replace physical verification. No original capture is modified.
Manufacturer documents are linked, not redistributed in this directory.

Validation completed on 2026-09-25: regenerating all analysis artifacts with
the recorded decoder produced byte-identical files; all six SHA256SUMS and
manifest hashes match; JSON files parse; relative documentation links resolve.
The original firmware checksum and the in-memory mutation check pass.
Online manufacturer references were consulted on the analysis date; unavailable
PRU datasheet mirrors were not treated as additional identification evidence.
