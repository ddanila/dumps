# Aquarius 2000 board reference

The board is marked “AQUARIUS 2000”, “MICROPROCESSOR CONTROLLED Q-METER” and © 1993 DIVERSA Ltd. It measures thermal energy using flow pulses and supply/return temperature sensors. TEPSO's February 1996 installation manual covers the base calculator in §6.2.1 and the two-flow 2000 A in §6.2.2. The dump's setup menu matches the base model. Both flow terminals exist on this PCB. [TEPSO installation manual, pp. 13–18](https://www.tepso.ee/failid/File/af2000instr.rus.pdf)

## Physical evidence

The owner's 20-photo archive has SHA-256 `0cba1d47df36d41156656afd3070f5f32b583a1ca852602cc20d304e09e2940a`. The following board views are resized from the indicated original filenames.

| View | Source filename | Visible details |
|---|---|---|
| [Under the display](../evidence/board/under-display.jpg) | PXL_20261123_155533631.jpg | Toshiba TMPZ84C011AF-6, KM62256ALP-10 SRAM, CAT93C46P, crystal marked 8.000000 / 30pF, 4.000 MHz silkscreen, socket marked 27C256 |
| [Component side](../evidence/board/component-side.jpg) | PXL_20261123_192350433.jpg | Two columns of four switches, LCD, round sounder, two trimmers, covered circuit, 2×4 service points, flow and Pt100 headers |
| [Solder side](../evidence/board/solder-side.jpg) | PXL_20261123_192358100.jpg | Switch contacts, connector solder joints and vias for continuity checks |
| [EPROM marking](../evidence/board/eprom.jpg) | PXL_20261123_192447914.MP.jpg | M27C256B, -15XF1, 9235E5. Use the socket notch and chip index when fitting a spare. |

With the LCD horizontal above the switches, the bottom six contacts read left to right **+5(BL), +5VCC, GND, FLOW2, GND, FLOW1**. The adjacent eight contacts are two four-wire groups, **SUPPLY Pt100** then **RETURN Pt100**. The backlight has its own supply contact. The 2×4 points next to the sounder correspond to the service diagram. The manual describes a destructive factory reset involving two of them. Normal exerciser operation uses the panel keys with the points open. The controls beneath the black cover, the trimmer functions, and the individual service-header nets still need tracing. [TEPSO, pp. 15–17](https://www.tepso.ee/failid/File/af2000instr.rus.pdf)

## Reset, memory and timing

The CPU's internal GPIO and four CTC channels account for all the verified I/O below. Toshiba specifies a crystal at twice CPU frequency, consistent with a nominal 4 MHz CPU here. Reset clears the port directions to input. Factory code at `3107h` configures every direction register. [Toshiba 1987 Microprocessors Vol. 1, printed pp. 784–786](https://ftpmirror.your.org/pub/misc/bitsavers/pdf/toshiba/_dataBooks/1987_Toshiba_Microprocessors_Volume_1_8bit_MPU_and_MCUs.pdf)

- **0000–7FFFh** holds the EPROM. Reset executes DI and a chain of absolute jumps from 0001h through 0112h and 2D72h to 3107h. The last nonzero byte is at 3FEDh. A linear disassembly also decodes data, including apparent OUT instructions in the table at 3B00h. Follow reset, interrupt vectors and subroutine callers before labeling a port.
- **8000–FFFFh** fits the photographed 32 KiB SRAM and the factory RAM test. Startup at 312Ch tests the low RAM page, then 314Ah sums bytes 0000–3FFFh modulo 65536, stores 0AE8h at 8080h, and compares retained words at 8300h and 8302h. A mismatch at the second comparison clears 8100–FFFFh. The factory stack starts at 8100h and grows downward. Factory RAM also holds the key FIFO at 8200h, working state around 8400h, samples at 862Ch, and history/measurement data including 9000h. The replacement uses only the low scratch page.
- **IM2** uses I=01h. Channel 0 ordinarily supplies vector 10h (0110h → factory 2526h), with control 87h and reload FAh. A prescaler of 16 and reload 250 give one interrupt per 4,000 CPU clocks, nominally 1 ms. During sensor acquisition the factory switches to vector 08h (0108h → 2197h). The time/calendar rollovers in 2626h–26B7h derive from software counters. The replacement displays nominal elapsed seconds and pauses them during an acquisition window.
- To inspect the same addresses locally, run `z80dasm -a -g 0 -o /tmp/aquarius.dis ../aquarius-2000-27256.bin` from this directory. The test suite runs the original machine instructions for the startup port writes, LCD transactions, EEPROM read and keypad scan.

## Firmware-visible hardware

Addresses are hexadecimal. Direction masks are the factory values and a set bit means output. Bit assignments to signals below come from executable code unless explicitly linked to a physical observation.

| Interface | Register and direction | Factory evidence and bench check |
|---|---|---|
| LCD data and control | PE 40h, direction 44h=FF. PB0 selects command/data, PB1 low for writes, PB2 enable | 2857h/2876h put a byte on PE and pulse enable. 319Fh sends 38, 01, 0C, 06 then loads custom glyphs. The two display rows use addresses 80h/C0h. Check both rows and the falling enable edge at the module. |
| Sounder | PB3 output, idle low | 2614h requests key feedback. 2535h toggles PB3 while the request is active and 25C3h clears it. The diagnostic drives a finite square wave. Compare PB3 with the round sounder's terminals and listen for a single chirp. |
| Periodic output | PB4 output | 253Bh toggles it each timer tick, including when sound is idle. The replacement preserves this behavior. Scope PB4 to establish its external load and the actual tick period. |
| Keys | PC 52h, direction 56h=00, pressed low | 25E5h samples all eight inputs, debounces them and reverses bit order into the FIFO. 2511h dequeues an event. See key table below. Verify contacts individually on the board. |
| Pt100 sampling | PD 30h, direction 34h=0F. CTC 10h–13h | 211Eh–21B0h selects 1/2 on PD0–1, asserts bit 3, configures CTC0 as an external counter, and collects 169 triples from channels 1–3. Factory then changes selector and sets PD2 for its next phase. The exerciser returns the last raw triple and restores startup PD=05. Compare results as one known resistance changes on each four-wire connector. Selector-to-connector order needs measurement. |
| Flow and other sampled inputs | PD4–7 inputs | 255Bh samples PD. 2562h–259Ah filters a falling transition on PD4. The exerciser counts falling transitions on all four inputs so FLOW1 and FLOW2 can be mapped independently. Connector conditioning, second-input routing and sensor voltage limits require circuit evidence. |
| Nonvolatile calibration/configuration | PA4 select, PA5 clock, PA6 data out, PA7 data in. PA direction 54h=76 | 2F25h, 2F6Eh and 302Eh read a 16-bit word. Eight command bits after the start bit encode READ and a six-bit address, matching the pictured CAT93C46P in 64×16 organization. Factory write paths begin at 2F85h/2FAAh. The exerciser emits only reads. Compare repeated values and clock traces. [CAT93C46 datasheet](https://media.digikey.com/pdf/Data%20Sheets/ON%20Semiconductor%20PDFs/CAT93C46_Rev2018.pdf) |
| Service/handshake | PB6 strobe, PB7 serial data, PA0 acknowledgment | 2727h–276Fh shifts bytes MSB first and waits for PA0. A separate factory interlock drives PA2 and checks PA0 at 02A5h/24D0h. The manual's service points are a candidate endpoint. Use continuity to locate these nets. The explicit diagnostic chord transmits 55h once with bounded waits. |
| Other GPIO | PB 51h, direction 55h=DF. PB5 input. PA1 output, PA3 input | 0C55h/0DE0h branch on PB5, including updating retained state. The PINS display exposes these levels. Inspect with a logic probe to establish external sources, PA1 load and any unused pins. |
| Backlight, covered circuitry, trimmers | Dedicated +5(BL) terminal and visible components | Check continuity from the backlight contact to the LCD and identify the trimmer endpoints. No independently established firmware backlight control. The covered circuit limits photographic net identification. |

## Button map

Orient the board as in the component-side photo. The positions come from TEPSO's service drawing. The factory codes follow the clock editor at 236Ch, setup cursor at 139Ah, erase confirmation at 0296h and dispatch at 013Bh. The emulator checks the raw-to-event conversion independently for every input. RESET is handled as a key event by the factory menu at 0283h. [TEPSO service drawing, printed p. 17](https://www.tepso.ee/failid/File/af2000instr.rus.pdf)

| Row | Left switch · pressed mask · factory code | Right switch · pressed mask · factory code |
|---|---|---|
| 1 | − · 80 · 01 | + · 02 · 40 |
| 2 | ← · 40 · 02 | → · 04 · 20 |
| 3 | SELECT · 10 · 08 | NORM · 08 · 10 |
| 4 | SETUP · 20 · 04 | RESET · 01 · 80 |

## Physical acceptance record

The owner reports that power is unavailable. No factory startup observation, probe capture, or replacement-ROM run has been recorded. TEPSO describes a self-test followed by clock setup on commissioning. This is an expected baseline.

1. On the available factory unit record the LCD text, key feedback, supply rails and CPU clock. Use a separate 27C256-compatible test EPROM or emulator for the diagnostic and retain the factory chip.
2. From cold start record the boot signature, both LCD rows, each button's printed name and pressed/released mask, and the SELECT chirp and quiet end state.
3. Record the four input counters before and after a known number of pulses on each identified flow input. Change one four-wire reference resistance at a time and record both CTC selector results. Verify tick frequency and EEPROM read repeatability.
4. Trace the service, sounder, backlight and unidentified GPIO connections before assigning connector pin numbers or electrical levels to them. Record connector orientation, stimulus, observed result and board revision with each verified mapping.
