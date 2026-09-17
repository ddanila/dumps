# Quick analysis and 8035 execution

Analyzed on 2026-09-17. The captured `4431 KBCL, LAT/CYR. 6800 U3`
image runs successfully in MAME 0.285's FACIT 4431 keyboard model.

## ROM structure

- Reset vector at `000` jumps to initialization at `753`.
- Timer interrupt vector at `007` services software serial communication,
  timing, LEDs, and sound. The code uses the 8035's two register banks.
- Initialization clears internal RAM and copies 15 initial state bytes from
  `792–7A0` to RAM `31–3F`.
- A distributed checksum routine (`0F8`, `1F8`, …, `6F8`, `7F5`) adds the
  ROM bytes modulo 256. The result is tested at `700`: nonzero enters error
  handling with code 1. **The complete dump sums to `00` modulo 256**, and
  emulation proceeds through this check into normal operation.
- The image mixes code and character tables. Table blocks include `104–154`,
  `204–2F6`, and `404–4F6`; the region beginning at `300` supplies another
  translation table. Three 27-byte variants at `204`, `21F`, and `23A`
  include the sequences `nh.v|qb\x60jcfx` and `NH>V\\QB@JCFX`.
- Normal matrix scanning is around `52D–557`, with key tracking/debounce
  routines following it. Transmission queues use RAM `10–17`.
- P1 bit 7 carries inverted serial output; the lower bits drive LEDs.
  P2 and external reads select the matrix, and external writes drive sound,
  according to MAME's keyboard hardware model.
- This is different from MAME's known keyboard ROM `11419660-00_kb31.u3`
  (CRC32 `45B90749`); this dump is `7AB50D44`. No byte-level comparison with
  that original image was performed.

The [disassembly](emulation/disassembly.txt) is a linear MAME disassembly of
all 2 KiB. Its apparent illegal instructions in table regions are data, not
evidence of execution failures. The sum and successful execution strongly
support a valid complete 2 KiB firmware image; they do not identify the
physical EPROM die or rule out unused capacity in a larger part.

## Emulator setup and observed results

The runner uses MAME's existing `f4431` machine and its real 6 MHz I8035
keyboard core, matrix, timer, and AY31015 serial link. Only the keyboard ROM
is authentic here. Temporary Z80 ROMs contain HALT instructions; other
terminal ROM regions are zero-filled placeholders. The main CPU never runs
terminal firmware. MAME's checksum warnings for those placeholders and the
replacement keyboard ROM are therefore expected.

The keyboard initially waits for the terminal. The harness sends byte `00`
through the terminal's emulated UART at about 1.099 seconds, then injects
the A matrix position (column A8, mask `20`) and Shift (A0, mask `04`).
Output is read from the receiving UART, not inferred solely from ROM tables.
The ROM and CPU state are not patched or forced past initialization.

| Emulated A0 strap bits 7–5 | Initial byte received | A position | Shift+A position |
|---|---|---|---|
| `E0` | `FF` | `61` (`a`) | `41` (`A`) |
| `C0` | `FF` | `66` | `46` |

Both four-second runs complete with **39,671 matrix reads**, continuing in
the normal scan loop. Key outputs arrive at about 1.975 and 2.670 seconds.
The host command travels through the emulated serial receiver and the key
bytes travel back through the emulated transmitter/UART.

The `C0` result demonstrates an alternate translation table. Interpreting
its bytes as specific Cyrillic glyphs requires the terminal's character
generator and mode conventions. The owner's LAT/CYR identification is
recorded, but a physical Latin/Cyrillic toggle sequence has not been verified.
The generic country names in MAME describe its original firmware and should
not be assumed correct for this ROM.

The harness supplies the strap bits directly on reads selecting A0, so they
are present even during the first boot-time matrix read. Other matrix bits
come from MAME's existing inputs. The owner's actual jumper positions were
not measured. Serial timings and keyboard matrix wiring follow MAME's model;
they have not been checked against this physical board with a logic analyzer.

## Reproduction

Requires `/usr/games/mame` with driver `f4431` and Lua/debugger support:

```sh
python3 facit/keyboard-2716/emulation/run.py
FACIT_COUNTRY=192 python3 facit/keyboard-2716/emulation/run.py
```

The runner asserts the three UART bytes for each of these two configurations
and fails on a Lua error or unsuccessful emulator exit. Each invocation
overwrites `emulation/probe.tsv`, `mame.log`, and `disassembly.txt`.
Saved runs are `latin.tsv` and `alternate-c0.tsv`, with corresponding MAME
logs. `FETCH` records count program-space reads, including table reads and
debugger disassembly, **not executed-instruction coverage**. P1 transitions
are sampled at program-space accesses.

Hardware-model source: sibling repo `mame/src/mame/facit/f4431_kbd.cpp` and
`f4431.cpp`, inspected at commit `5c9b7aa55b298439941e8f75a07c685d2f5bd73c`.
The executable used is the installed MAME 0.285, not a new build of that repo.
