# ROM dumps

This repository preserves ROM images recovered from physical hardware. Sets
whose originating system is not known are kept under [`unknown/`](unknown/)
with chip markings, physical placement, acquisition details, and checksums.
Attributed sets are grouped by system; individual READMEs record identification
confidence and any unresolved provenance.

## Sets

- [`Cirrus Logic GD-5422 VGA BIOS`](unknown/cirrus-gd5422-27512-20260921/) —
  version 1.00d, embedded date 08/07/92; single 64 KiB capture with a valid
  32 KiB option-ROM checksum and zero-filled upper half.

- [`Juku / EktaSoft 3.7 low EEPROM control`](juku/ekta37-low-control-20260919/) —
  two 8 KiB reads exactly match the known D15 image; programmer control check.

- [`FACIT 4431 LAT/CYR keyboard`](facit/keyboard-2716/) — repeat-read 2 KiB
  ROM labelled `4431 KBCL, LAT/CYR. 6800 U3`, from an English/Russian
  keyboard with an Intel 8035. Internal checksum passes; MAME execution
  confirms matrix scanning and serial key output for two layout settings.
- [`Estafeta-03 / TMS2764 LHP8749 set`](estafeta-03/tms2764-lhp8749/) — two
  repeat-read 8 KiB EPROMs; confirmed 8086-compatible code and an
  `ЭСТАФЕТА - III` banner. Strong Estafeta-03 family attribution; exact board
  provenance and firmware revision remain unconfirmed.
- [`K573RF5 set 41-44`](unknown/k573rf5-set-41-44/) — four 2 KiB EPROMs from
  an unidentified board, reported not to be from a Juku computer. Sequential
  8080-compatible code with passing internal checksums; likely programmable
  instrumentation with a GPIB-style interface and signed-decimal messages.

## Rights

No license is asserted over the dumped firmware images. They may contain
copyrighted software belonging to unidentified rights holders. Metadata and
checksums are supplied for identification, preservation, and research.

## Acquisition investigations

- [RF5 recheck and CPU survey](unknown/rf5-plastic-20260920-recheck/) —
  two matching nonblank reads; identity unresolved.
- [Programmer-output echo model](analysis/20260919-programmer-echo/) and
  [27256 CE-state audit](analysis/20260920-27256-ce-audit/) — distinguish
  anomalous captures from chip contents and document the reader correction.
- [Third 27256](unknown/27256-20260920-chip03/) — single FF/F7-only capture;
  stored-data validity remains unresolved.
- [Blank 27256 read records](analysis/20260921-27256-blank-records/) —
  metadata only; all-FF binaries are excluded.
