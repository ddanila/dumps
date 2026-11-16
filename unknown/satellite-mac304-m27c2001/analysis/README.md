# MAC4 / MAC 3.04 firmware investigation

Analysis of the unchanged 256 KiB M27C2001 image acquired on 2026-11-16.
The chip sticker reads **MAC4 / V:3.04** and the ROM identifies its MAC
software as **3.04, 1993-10-13**. The original receiver is not available.

**Result:** probable Nokia MAC4-family firmware, using banked 8051 code and
Intermetall-compatible MAC/video controls. Original code boots under synthetic
peripherals and executes the recovered menu, service and navigation fixtures.
The investigation found a hidden service gate, detailed calibration editors,
and an Italian/Spanish translation mix-up; exact receiver model and full
hardware behavior remain unconfirmed.

Start with the [searchable text catalog](menus/out/catalog.html),
[captured menu gallery](emulation/output/gallery/index.html),
[execution summary](emulation/output/SUMMARY.json), or
[reproduction instructions](emulation/README.md). HTML files work offline when
opened locally; GitHub displays their source.

## Evidence and scope

The physical acquisition is two identical reads, SHA-256
`8bea3d9a252bcb72c86594d4bed711c56cba43158baf454b0f53ba189e564d8a`,
CRC32 `8012f03b`. Reproduction scripts check this exact revision before
interpreting addresses. Offsets are physical file offsets unless marked CPU.

Four different kinds of evidence must not be conflated:

- **Bytes:** strings, pointers, opcodes and data present in the ROM.
- **Static interpretation:** decoded code paths and inferred data structures.
- **Executed:** original instructions run by the emulator, under recorded inputs.
- **Hardware assumption:** simulated peripherals or seeded state that replace
  missing receiver components. This cannot establish RF reception or real
  conditional-access operation.

## Physical ROM and processor

The owner supplied [the original chip photo](../photos/PXL_20261116_173434247.jpg).
Package markings: ST `M27C2001 -15F1`, `V88AB`, `9348C`, `SINGAPORE`.
The sticker's lower identifier is worn and has not been reliably transcribed.
The firmware banner is at file `0x63E6`:
`FRONT:xxx   MAC:3.04  93-10-13`.

The reset vector is an 8051 `LJMP 002Eh`. Startup clears external RAM
`6000h–7FFFh` and internal RAM, initializes the register-bank bits and stack,
and enters banked code. The I²C register group at SFR `D8h–DBh` and the
interrupt vector at `002Bh` are consistent with a Philips 80C652-compatible
controller. This identifies a peripheral architecture, not a unique chip
marking; related derivatives share it. The
[Philips 80C652/83C652 datasheet](https://www.ic-components.nl/files/5a/P80C652EBA-04,512.pdf)
documents the matching S1CON/S1STA/S1DAT/S1ADR registers and I²C pins.

The image contains 153,542 bytes before its all-zero tail begins at `0x257C6`;
the remaining 108,602 bytes are zero. Interior zeros are also present. This
boundary is a byte-level observation, not a declared program-length field.
No whole-image repetition is present at the tested power-of-two periods.
See [inventory.json](inventory.json), reproduced with:

```sh
python3 inventory.py --output inventory.json
```

The inferred code mapping uses a fixed lower 32 KiB and an upper 32 KiB
window. A write to external address `8000h` selects the window. The far-call
wrapper at common CPU `07C5h` writes `(bank + 1) << 4`, preserving the caller's
bank and status. Four populated windows occupy physical `08000h–27FFFh`;
the last window contains the start of the zero tail.

| Region | CPU address | File offset | Selection |
|---|---|---|---|
| Common code, strings and tables | `0000–7FFF` | `00000–07FFF` | Always mapped |
| Bank 0 | `8000–FFFF` | `08000–0FFFF` | Latch `10h` |
| Bank 1 | `8000–FFFF` | `10000–17FFF` | Latch `20h` |
| Bank 2 | `8000–FFFF` | `18000–1FFFF` | Latch `30h` |
| Bank 3 | `8000–FFFF` | `20000–27FFF` | Latch `40h` |
| Remaining capacity | Not established | `28000–3FFFF` | All zero |

## Receiver attribution

The sticker, ten-language interface and satellite/MAC menu content support a
Nokia MAC4-family attribution. A contemporary retailer advertisement in the
[November 1992 satellite reception supplement](https://retronik.silicium.org/DOCUMENTS/revues/haut-parleur/1992/HP1806_11-1992_Supplement_Guide_pratique_reception_TV_par_satellite.pdf)
lists Nokia MAC4 SAT2002/SAT2202 and a related DEC3002 decoder. The branding
alone does not identify which receiver, decoder or compatible board supplied
this EPROM. No exact reference image has been located.

## Peripheral-family evidence

The service labels are unusually specific: `EDC DMA198`, `PLL gain DMA199`,
`Slice level DMA199`, `VCO DMA14`, `Color Vsat DMA23`, and `Luma delay DMA200`.
Those register numbers and purposes match the manufacturer's
[DMA 2271/2280/2281 C/D/D2-MAC decoder datasheet](https://elektronikjk.com/elementy_czynne/IC/DMA2281.pdf),
tables 4–1 and 4–3. For example, register 198 contains energy-dispersal
compensation and register 199 contains PLL gain and slice-level controls.
This supports the Intermetall MAC-decoder family; it does not distinguish
which compatible decoder chip is fitted. The accompanying VCU, TPU and audio
labels refer to further video, text/display and audio controls.

Common routines beginning at `019Dh` shift bits on P1.0 and clock P1.1;
other routines use P1.2 as a control signal. Their shape and the register
labels support an IM-bus interpretation. Actual pin wiring and peripheral
responses still require a board or schematic. They must not be mistaken for
ordinary flat RAM merely because the emulator can store values there.

## Feature inventory from the menu resources

These functions and choices are present in the ROM's structured resources.
Availability on a particular receiver can depend on its front controller,
option byte, card state and attached hardware. Runtime results below identify
which paths have additionally been exercised.

| Area | Present functions / choices | Representative file evidence |
|---|---|---|
| Main interface | Main menu, favourites, installation, clock, timer, audio, access | `5DD3–61D8` |
| Channel setup | Channel number, fine tuning, satellite band, polarity switch, antenna input, 0/12 V switch, programme name, magnetic polarizer, video level, decoder, audio, antenna position, video filter, card selection, AFC | `5913–59C4` |
| Channel choices | Low/medium/high, radio, 0/3/6/9/12 V, decoder choices d1–d6, V/H, RGB and S-Video | Table B entries 56–100 |
| Installation | Channel Programming, System Programming, Start Scan | `5E25–5E63` |
| System setup | Primary and alternate language, homing, LNB standby, colour, contrast, sharpness, TV output/switch, polarity type, baseband input/de-emphasis, menu-button activation | `61D9–628C` |
| Bands and video | Dual-band inputs, low-band inputs, TV format, satellite-band adjustment, Phono/Scart, PAL/MAC/Flat | `628D–6383` |
| Favourites | Favourites list, favourite number, programme-selection/navigation text | `5EFF–5FC2`, `614A–61D8` |
| Clock and timer | Day/time, seven weekdays, programme and event numbers, start/stop, today/weekly, first/second, overlap warning | `5AA8–5C85`, `600B–6149` |
| Audio | Balance, left/right, external inputs 1–4, MAC radio, D-MAC and D2-MAC labels, mono/Panda/stereo/J17 presets | `521E–537B`, `663B–6681` |
| Subtitles and text | Subtitle page, off, auto-select, PAL notice directing users to their television's teletext | `537C–5912` |
| Card access | Issuer, card selection, access control, subscription/consultation, PPV lock, consultation lock, parental control, code change | `2FCF–3555`, `3B1D–3C73` |
| Purchases / account | Prebooked and impulse PPV, token credit, overdraft, purchase confirmation, price, maturity rating | `3BAC–43C6` |
| Access errors | No access, overdraft reached, missing card, check card, smart-card error, geographic blackout, no information | `43C7–48C2` |
| Programme information | From/to, theme, level, class, price, programme, paging/navigation, months, 17 genre slots | `48C3–521D` |
| Receiver service | Three video gains, 13 V and 18 V calibration, volume, option byte, Change Code | Eight records at `778E–77CD` |
| MAC service | 21 video/decoder/audio/text calibration records, bit patterns, white/black levels, frame and bit-error diagnostics | `6489–6504`, `77CE–7A04` |

The genre structure contains a blank slot plus Arts, Children, Club,
Entertainment, Film, Lifestyle, Music, News, Series, Sports, Special, Nature,
Documentary, Miniseries, Science and ALL. A string's presence alone is not
proof that a current signal/card can supply that category.

The main text pool contains genuine language-independent English material.
In particular, Channel Programming and System Programming fields are shared
rather than supplied as ten translations. The service calibration labels
are also shared. The catalog preserves this distinction instead of inventing
translations that are absent from the firmware.

## Hidden service entry and editors

The table-driven service recognizer is bank 3 CPU `AD43h` (file `22D43h`).
Its default internal event sequence is **`06h → 0Ah → 08h`**. These are
internal event IDs, **not a verified sequence of physical remote buttons**.
The state byte is XDATA `77C0h`; the comparison table is XDATA `77C1h–77C4h`.
The first match starts a 50-tick countdown at XDATA `68DEh`; Timer 0 decrements
it. A wrong event resets the recognizer and an expired countdown rejects the
final event. No wall-clock duration is asserted without the crystal frequency.
The ordinary caller at file `233E5h` changes the top-level mode to 5 after
success, initializes the display and invokes the service dispatcher.

The receiver-service **Change Code** field is a different mechanism. Its
special save path writes four characters through front-controller settings
`31h–34h`; the traced path does not replace the hidden recognizer's event
table. A relationship to receiver locking is plausible, but the field has
not been established as a smart-card PIN. The literal `1234` displayed by the
editor must not be advertised as the hidden service-entry password.

The receiver's **Option Byte** is setting `30h`, default `3Dh`, with individual
bit editing. Its locally traced apply case is a no-op; saving sends it to the
front controller. The names/meaning of its eight bits remain unresolved.
The other service settings expose PAL/MAC/CVBS gain, 13 V and 18 V calibration,
volume, and the detailed MAC/video/text controls listed in the catalog.

A second recognizer caller exists in the startup path (bank 1 CPU `FF93h`).
It translates incoming events through another table and selects different
startup actions. The service-screen behavior must not be generalized to that
path without further state and hardware validation.

Detailed addresses, data structures and caveats are in
[code/REPORT.txt](code/REPORT.txt), with a curated
[function map](code/functions.json), [far-call pattern inventory](code/far_calls.tsv)
and [targeted disassembly](code/evidence.asm). The call-pattern inventory is
not a complete reachable-call graph: dynamic setup is omitted and byte-pattern
matches in data are possible.

## Complete text catalog and language mapping

The [offline searchable catalog](menus/out/catalog.html) preserves every
identified main-table slot, including blank strings, short labels, control
bytes and aliases. The [all-language matrix](menus/out/all_languages.tsv)
places translations side by side; [catalog.json](menus/out/catalog.json)
records exact bytes, pointer addresses, targets and grouping evidence.

There are **1,424 main pointer slots**: **130 groups of ten languages** and
**124 shared slots**, pointing to 1,075 distinct locations. The language order
is English, Swedish, Danish, Norwegian, Finnish, Dutch, German, French,
Italian and Spanish. An additional 35 structural pointers cover language names,
PAL audio choices and service labels. All 14,074 bytes of the identified main
string pool are preserved, including unreferenced fragments and terminators.
The [static report](menus/ANALYSIS.txt) describes each table and its consumers;
[code-reference records](menus/out/table_code_refs.json) link recognized
selection patterns to resource slots. These are bounded pattern matches, not
an exhaustive proof of reachability for every string.

The font is external to this dump. The real OSD initializer selects six
national subsets for ten languages; Swedish, Danish, Norwegian and Finnish
share one subset. The catalog defaults to exact byte spelling. Its optional
Unicode normalization is a linguistic aid, **not a recovered hardware font**;
for example, different proposed Nordic letters for the same byte cannot all
be the physical glyph under one unchanged subset.

One translation defect is preserved: the Italian overdraft heading points to
Spanish `Giro en descubierto`, while the Spanish heading points to Italian
`Ammontare scoperto`. Their following lines are in the correct languages.
The pointers are A257/A258 at `6985h/6988h`, targeting `3E88h/3E9Ch`.

## Calibration behavior

The service handlers contain behavior that simple range labels conceal.
Receiver numeric edits add a signed byte to a 16-bit intermediate and then
compare unsigned bounds. Decrementing zero therefore produces `FFFFh` and
can return to zero rather than wrapping to the maximum. MAC fields instead
check thresholds before adding the stored step, without a universal final
clamp. Contrast can advance from `F9h` to `FDh` despite an upper threshold of
`FCh`, then stop. VCO uses signed saturation; zero-step fields rely on bit
editing rather than numeric increments.

The [471 generated test specifications](code/service-tests.json) are static
expectations. Their execution results are recorded separately by the emulator.
They test selected scratch values and editor/save behavior, not calibrated
voltages or picture quality. Some fields have coupled side effects, notably
colour controls; a passing selected-byte assertion does not prove every
coupled register's physical effect.

## Executing the original firmware

The [emulator package](emulation/README.md) uses a vendored MIT-licensed
8051 core with documented stack/timing corrections, a bank latch, and a
synthetic peripheral model. It runs the original reset path to the main
scheduler. No ROM bytes are patched and no original instructions are skipped.
The test harness then injects documented routine calls through the firmware's
own banked-call wrapper and records display writes, settings writes and state.
This is controlled execution of real code, not a recreation of the menus.

The mock front controller delivers I²C slave interrupts and replies shaped to
match the firmware's pending command and expected length, mostly with zero
payloads. P1.0 reads zero to model the missing IM-bus device. The resulting
execution proves behavior under these assumptions, not compatibility with a
real front controller. Call fixtures can seed XRAM fields; those inputs are
recorded with each experiment.

The [OSD gallery](emulation/output/gallery/index.html) shows captured character
memory as a readable ASCII approximation. It preserves display memory between
calls, so incremental writers retain earlier content. Controls and national
glyphs are not rendered as authentic pixels; raw bytes remain in the linked
JSON. The gallery includes service-page scrolling and all ten language settings.

Verification distinguishes three questions:

1. Directly injecting all **1,424 table pointers** checks that the original
   text routine emits exactly the extracted bytes. It does not independently
   prove which language or screen selects each pointer.
2. Calling real screen routines with ten language indices checks actual
   selection paths and runs the OSD subset initializer. Hooks observed **252
   group/language pairs across 27 resource groups**; a frozen regression set
   also records 36 intentional fixed-English selections in shared setup/service
   screens. This does not independently execute every one of the 130 language
   groups. There are **310 bounded
   cases**, comprising 31 renderer/component/action fixtures times ten
   languages. This includes a scan-start action and a no-output editor candidate;
   it is not a count of 31 independently proven full menus.
3. Service-editor tests and navigation scenarios check state changes under
   explicit inputs. **471 service cases** cover numeric boundaries, bit editing
   and Change Code save behavior. The dispatch tests exercise every cell of
   the two recovered matrices: **154 top-level** and **165 submenu** scenarios.
   Five top-level event-7 cases set PCON power-down and intentionally do not
   return; the other 314 return. Each scenario begins from a reset-derived
   state with the selected matrix state/event injected, rather than following
   every possible history through the real user interface.

The hidden-entry experiment exercises the ordinary caller, reaching top-level
service mode 5 and producing SERVICE MENU. Separate wrong-input and timeout
fixtures reject entry. Scrolling captures all 21 MAC rows. The credit renderer
also reproduces the Italian/Spanish heading defect. Detailed results and
assertions are in [SUMMARY.json](emulation/output/SUMMARY.json) and the linked
[per-case results](emulation/output/results/).

## What remains unproven

This is a reproducible investigation of one ROM, not a complete emulation of
the receiver. The front controller, tuner, satellite signal, demodulator,
smart card, nonvolatile settings store and physical OSD font are unavailable.
The adaptive peripheral replies deliberately satisfy firmware expectations;
they are not independent evidence that the real protocol works that way.
Displayed `FRONT:  0`, readings, prices and card records are synthetic.

All identified main resource slots are extracted, but no finite set of seeded
screen calls establishes every possible receiver state. Broadcast text and
card-supplied strings are outside the ROM catalog. The `Start Scan` resource
has no proven standalone renderer: its candidate action sets scan state, but
no RF scan is simulated. A candidate editor routine returns without text;
that alone does not identify a working screen. Startup service variants,
option-bit meanings, the exact remote-button mapping, and the firmware's own
integrity check remain unresolved. No exact external binary match or exact
receiver model has been confirmed.

## Reproduction

From this analysis directory:

```sh
python3 inventory.py --output /tmp/mac304-inventory.json
python3 menus/extract.py ../mac304-m27c2001.bin --out /tmp/mac304-catalog
python3 emulation/run_all.py --rom ../mac304-m27c2001.bin --out /tmp/mac304-execution
```

Python 3 and a C compiler are sufficient for extraction and execution. Add
`--disassemble` to the extractor to reproduce optional linear evidence excerpts
with radare2 (used here: 6.0.7). The curated code inventory can be regenerated
with `python3 code/analyze.py --out /tmp/mac304-code` (requires radare2), and
static editor specifications with
`python3 code/service_tests.py --out /tmp/mac304-service-specs`.
The scripts reject a different ROM revision. Detailed harness commands and
mock levels are in [emulation/README.txt](emulation/README.txt).

The published catalog and optional disassembly exports were regenerated in a
separate directory and compared byte-for-byte: all 56 files agreed. The
integrated emulator suite was run from the repository sources; the core's
stack/timing checks and the bounded firmware assertions passed. Browser checks
covered catalog filtering and gallery screen/language selection. These checks
establish reproducibility within the stated model, not exhaustive firmware or
hardware correctness.
