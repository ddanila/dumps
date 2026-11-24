# Beckman DU-7 HS firmware analysis

2026-11-07. Static analysis of seven plausible captures and anomalous U104;
no successful emulator boot or physical repeat verification is claimed.

## Identification

U102 offset 003A names Beckman Instruments; 0269 says DU-7 HS Operating
Instructions. This strongly identifies a UV/visible laboratory spectrophotometer.
It measures transmission through samples, compares against a background/reference,
and displays absorbance, spectra and derived concentrations.

The supplied [auction](https://www.osta.ee/vana-arvuti-plaat-detailidega-259997212.html)
is item 259997212, titled “Vana arvuti plaat detailidega” (old computer board with
components). Its text does not identify the instrument. The canonical indexed
page was accessible; the supplied query URL was not. Listing photos have not
been independently inspected.

[Beckman's history](https://www.beckman.fr/about-us/company-history/product-timeline)
dates the DU-7 family to 1981. The
[Beckman archival photograph record](https://digital.sciencehistory.org/works/000000239/viewer/z603qx727)
describes its microprocessor and built-in graphics display. This dates the
product family, not these ROM revisions. No firmware build date was decoded.

## Functions recovered from ROM

U102's instructions explain turning on UV/VIS sources, choosing one of six
modes, editing parameters with arrow/numeric/SEL/enter keys, START to calibrate,
and RUN to measure a sample. This is dedicated instrument firmware, not a PC BIOS.

| U102 file offsets | Evidence and functionality |
| --- | --- |
| 045C–04E5 | Absorbance, sources, single/scan/repeated scan/time/remote modes |
| 05BE | Concentration |
| 07B8–085F | Scan count, interval, time drive, total time |
| 08D7–08F8 | Calculation, upper and lower limits |
| 09A6, 0AA8 | Standard and factor parameters |
| 18CB, 1917 | Program/scan lists, wavelengths, functions and units |
| 1A5B | Insert standard/sample/background prompts |
| 1BB3–1BE5 | Calibration, background scan, measurement, sample scan |
| 1BF6 onward | Screen copying, first/second derivative, log A, peak picking, net absorbance, overlay |
| 1F36 | Peaks and area |

Spectroscopy interpretation: T=I/I0, percent transmission=100T, absorbance=-log10(T).
The ABS/%T menu corresponds to these quantities; the actual numerical routine
has not been fully traced. Scans produce spectra, time drive/kinetics observes
changes over time, and standard/factor modes support quantitative concentration
analysis. Menu presence does not prove every optional package is enabled.

The accessory catalogue names autosamplers, sippers, multicomponent analysis,
high-resolution graphics, expanded spectral storage, Safe Memory, RS-232 I/O
and calibration accessories. This advertises options; it does not establish
which accessories were connected to this board.

Errors include low energy, source not on, UV/visible source failures, out of
range, invalid format, incompatible scan, invalid derivative calculation,
file missing/already exists, insufficient memory and temporary memory full.
U103 adds “Unblock the beam”. The firmware coordinates optical measurement,
user interaction, data storage and processing. Specific ADC, motor, display and
interface ICs have not been established.

## Inferred software map

The owner-reported 8088 is consistent with decoded 16-bit x86 instructions.
Its 8-bit external bus does not require even/odd interleaving. Many ROMs begin
with E9 near-jump tables, providing stable module entry points.

| Position | Size | Inferred runtime placement | Part/revision text |
| --- | ---: | --- | --- |
| U101 | 4 KiB | F000:F000–FFFF | 594261 A |
| U102 | 8 KiB | F000:6000–7FFF | 594262 H |
| U103 | 4 KiB | F000:D000–DFFF | 594263 H |
| U104 | 4 KiB anomalous | C000–CFFF is the leading missing-module hypothesis | unreadable |
| U105 | 4 KiB | F000:B000–BFFF | 594265 K |
| U106 | 4 KiB | F000:A000–AFFF | 594266 H |
| U107 | 4 KiB | E000:0000–0FFF, likely | 594267 H |
| U108 | 8 KiB | F000:8000–9FFF | 596498 J |

Physical addresses equal segment*16+offset. This is software inference, not a
measured decoder map; mirrors and expansion windows remain unknown.

U103 local 05CF references CS:D5D5, matching its local 05D5 table. U105
references B285/B28A; U106 references A0AF/A0FC; U108 references 889F/955B.
U102's base is supported by pointers to its menus, including 6266/6452.
U107's local entry table and RETF functions match U108's explicit E000 far calls.

The capacity mixture is plausible: larger menu and application modules coexist
with smaller service modules. Part numbers 594261/2/3/5/6/7 follow observed
socket numbering. U108's different number might reflect module or revision
history; it does not demonstrate a misplaced chip. The owner's possible
prior-reseating concern remains recorded. Do not rearrange chips based solely
on mixed capacities, and do not concatenate 1–8 as a CPU image.

Earlier strings output `594265 KH*` and `596498 JQ"` included the final two
binary trailer bytes. They should not automatically be interpreted as revision
suffixes. Their purpose/checksum algorithm is unresolved; byte-sum calculations
do not establish a valid checksum.

## Reset and main loop

U101 local 0FF0 contains FA EA 00 80 00 F0: CLI and far JMP F000:8000.
This occupies the CPU reset vector if U101 maps to physical FF000–FFFFF.
U108 at 8000 jumps to 811D, clears AX, sets DS/SS/ES=0, sets SP=812B, then
jumps D045. U103 at D045 jumps DD70. This links three separate captures and
strongly supports the map. The unusual initial SP must not be assumed to be
an ordinary initialized RAM stack without following the startup routine.

U108 8145 calls a RAM-held function pointer, then repeatedly calls C000;
C003 is also called, and returned AL bits select handlers. This suggests
input/event handling, plausibly keyboard services, in the missing module.
The exact semantics require its real code. U108 has wrappers calling
E000:0024, 0027, 002A and further entries, consistent with U107 services.
U103 contains direct IN/OUT routines and initialization code.

These observations support modular bare-metal firmware. No operating system,
complete boot, hardware-accurate emulation or reconstructed display is claimed.
Filling C000 with invented bytes would not recover the missing functionality.

## Quality, limitations and next steps

40 KiB was captured; 36 KiB across seven chips looks plausible. Each plausible
chip has one physical read only. U104 has two identical reads: initial 00 then
alternating 06/04. This resembles a read-path/address echo, but does not establish
the electrical cause or prove a dead chip. Contacts, exact marking and routing
remain candidates. Its likely C000 services make recovery important for emulation.

Targeted searches for Beckman 594261 ROM and DU-7 ROM/firmware found no matching
image. This is not an exhaustive collection/hash comparison or proof of novelty.
Original captures remain local; parent manifest records hashes and session paths.

Reproduce with `python3 analysis/analyze.py` from this acquisition directory.
It writes hash/string evidence and linear ndisasm output to /tmp/beckman-analysis;
--sessions and --output override paths. Linear decoding also decodes data as
instructions; only contextual code excerpts above are interpreted as code.

Next priorities: recover U104 using its exact marking and verified contacts,
independently repeat the seven plausible captures, inspect board photos/decoder
circuitry to validate mapping, then emulate with explicit I/O models. Exact
hardware registers, numerical algorithms, optional-package gating and all boot
branches remain open reverse-engineering work.
