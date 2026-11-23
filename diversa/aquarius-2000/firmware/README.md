# Aquarius 2000 board exerciser

A standalone 32 KiB Z80 diagnostic ROM for the Diversa processor board. The first row shows `AQ2000 BOARD TEST` on startup, then the name of the last button pressed. The first two characters of the second row show the current pressed mask in hex. Release all keys to return the mask to `00`. Diagnostic readings remain visible after release. The board is currently unpowered. All execution results below are software tests.

[Ready-to-program image](aquarius-exerciser.bin) · [Hardware reference, button positions and bench procedure](HARDWARE.md)

## Build and verify

From this directory, run:

```sh
make test
cmp build/aquarius-exerciser.bin aquarius-exerciser.bin
(cd build && sha256sum -c SHA256SUMS)
```

`make` needs GNU Make and z80asm. It builds from the two assembly sources, fills unused EPROM bytes with FF, and emits the ROM, symbol map and SHA-256 file under `build/`. Tests also need a C compiler, libz80ex development headers/library and the preserved factory dump one directory up. The prebuilt ROM can be checked against an independent build with the comparison above.

## Operating the diagnostic

| Key | Pressed mask | Reading or action |
|---|---:|---|
| RESET | 01 | Shows the preceding stable mask. Useful for testing chords and releases. |
| + | 02 | Four adjacent two-digit falling-edge counts, in PD4, PD5, PD6, PD7 order. Each wraps at 256. Use to identify flow input routing. |
| → | 04 | Starts one sensor capture using selector 1 or 2, alternating per press. Shows the last sampled CTC1, CTC2 and CTC3 bytes after 169 interrupts, or TIMEOUT when the trigger is missing. |
| NORM | 08 | Shows the low 16 bits of the tick count and elapsed nominal seconds, separated by a slash. Both fields are hex. Acquisition temporarily repurposes the timer. |
| SELECT | 10 | Produces one 96-transition chirp on PB3. A held key produces one chirp until released and pressed again. |
| SETUP | 20 | Shows PD, PA and PB readback as three hex bytes, then the last service-link result. |
| ← | 40 | Displays one 16-bit EEPROM word. Each press advances through word addresses 00–3F with wraparound. A missing ready signal displays TIMEOUT. |
| − | 80 | Tests SRAM byte 8070h with 55h and AAh, restores its original value, and displays pass/fail. |
| SELECT and plus | 12 | Plays the JukuPoly Canyon arrangement. RESET stops playback. |
| SELECT and minus | 90 | Plays the JukuPoly Suspense arrangement. RESET stops playback. |
| SETUP + RESET | 21 | Sends one 55h test byte over the factory-style handshake. The PINS status is 00 before testing, 01 on acknowledgment, or FF on timeout. Scope PB6/PB7 and PA0 to locate the physical endpoint. |

For simultaneous presses the full mask is displayed. The lowest newly pressed bit selects the diagnostic, except for the three diagnostic chords. The input scan is polled and debounced independently of CTC interrupts. The firmware does not implement heat billing, calendar setup, history or factory reset.

## Reusing the drivers

`exerciser.asm` owns vectors, scratch RAM, the foreground poller and the user interface. `board.asm` supplies the GPIO setup, LCD strobes, CTC, sounder, EEPROM and handshake routines. Use the generated symbols when debugging. Keep the stack at 8100h and reserve the board driver's labeled scratch bytes if reusing these routines.

| Entry | Input and result |
|---|---|
| board_init, lcd_init | Call with interrupts disabled at startup. Initialize GPIO before the LCD. Install IM2 vectors, call tick_start and set irq_live before enabling interrupts. |
| lcd_command, lcd_data | Byte in A. Foreground calls preserve BC, DE and HL. Control writes preserve PB3–7 and keep interrupts masked across the strobe. lcd_command resets the UI column counter. |
| lcd_text, hex_byte | HL points to a zero-terminated ASCII string, or A holds the byte to print as two hex digits. lcd_text advances HL to the terminator. |
| chirp, link_probe | Foreground routines with interrupts enabled. chirp returns PB3 low. link_probe updates link_status and idles PB6–7 on completion or timeout. |
| capture | Foreground only. Alternates channel, updates capture1–3, leaves remaining zero on success. Restores PD=05h and the periodic interrupt on either outcome. |
| nv_word | A is the word address 0–63. Returns HL and carry clear on success, carry set on timeout. Clobbers AF, BC, DE and HL. Leaves select low and preserves PA1–2. |

## What the tests establish

The harness executes original and replacement machine code with libz80ex. It compares the first eight GPIO writes from both reset paths, command/data LCD strobes, and the EEPROM read waveform at every word address. It verifies that reads preserve the other enabled port-A outputs. The factory timer ISR is entered with a scan due and each active-low key is followed through the real factory event FIFO.

The replacement boots from PC=0 with patterned SRAM. The harness decodes LCD writes, injects keys and contact bounce, checks IM2 delivery, falling-edge counts, elapsed seconds, sound termination, handshake bits, SRAM restoration and bounded waits for missing devices. GPIO readback, LCD storage, known EEPROM bits, acknowledgment, external counter triggers and sample bytes are supplied by the harness. Tests do not measure oscillator accuracy, sound volume, display settling, sensor transfer functions or electrical connector levels.


## JukuPoly music

Hold SELECT and press the plus key for George Stone’s *Trip Through the Grand Canyon*, or the minus key for Bobby Prince’s *Suspense* (DOOM E1M5). Release the keys once the title appears. RESET stops the player at the next 20 ms frame boundary. Each arrangement plays once and returns to the sound diagnostic. Build both listening previews with `make preview`. The WAVs in `build/` reproduce the emulated Aquarius PB3 waveform with DC removal and normalized playback level.

The ROM interprets the original flat JukuPoly v1 rows, maintains three independent phase accumulators, applies envelopes, legato and slide, and mixes the percussion samples. The GPIO backend emits a single variable-width PB3 pulse per nonzero sample. At 4 MHz a level of 1–15 produces 6.5–20.5 μs high. The Juku D57 hardware produced longer impulses, so the acoustic level and tone color can differ. A free-running read of CTC0 paces the mix at nominally 7,200 samples/s. The normal millisecond interrupt stays enabled between pulses. Playback scratch begins at 801Bh, below the diagnostic SRAM test at 8070h.

The regression runs each track through the panel entry point. It decodes every PB3 pulse back into a four-bit level, including silent sample slots, checks the sequence against the original Juku player, and verifies shared port bits, completion time, key abort and quiet return. Reference digests are FNV-1a over one unsigned byte per sample. In the original Canyon and Suspense COMs the mixed nibble is in A at PC 0162h, immediately before the zero test. The reference run used the source project’s i8080 core and recorded A there through return to CP/M.

| Arrangement | Samples | Original Juku mix digest | Credit |
|---|---:|---|---|
| Canyon, 40-row opening | 53,136 | 4423b818 | George Stone, Canyon Music. Source credits © 1991 Passport Designs, Inc., produced by The Music Data Company. |
| Suspense, first-minute arrangement | 432,000 | fda63514 | Robert (Bobby) Prince, DOOM, id Software. |

The two score includes are drawn from `firmware/jukupoly-song-generated.inc` and `firmware/jukupoly-suspense-generated.inc` in the pinned JukuPoly tree. Each is copied from `jukupoly_song_rows:` to end of file, with the `jukupoly_` label prefix renamed to `canyon_` or `suspense_` for linking both into one ROM. The score bytes and drum samples retain their original meanings. [JukuPoly source, score provenance and credits](https://github.com/ddanila/8080-cosim/tree/a0a47d8da3329fe1ea78f6a0c6e8f46b0adfcd94/spinoffs/jukupoly)
