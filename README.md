# ROM dumps

This repository preserves ROM images recovered from physical hardware. Sets
whose originating system is not known are kept under [`unknown/`](unknown/)
with chip markings, physical placement, acquisition details, and checksums.
Attributed sets are grouped by system; individual READMEs record identification
confidence and any unresolved provenance.

The preservation target is firmware not already available in public Internet
collections. Compare new acquisitions against existing dumps before adding
them. Exact known matches, including matches after removing padding or
converting documented byte layouts, stay in local acquisition sessions rather
than the firmware collection. Keep all-FF captures local as well.

## Sets

- [Award VENUS-VIA 1993-04-14](unknown/award-venus-via-19930414/) —
  unidentified-board 128 KiB Award 4.20 BIOS with Cirrus VGA; matching large
  and small reads, no exact full-image match established in checked archives.

- [MB007 integrated video BIOS Low / High pair](unknown/mb007-video-bios/) — two matching
  16 KiB reads per chip; reconstructed Chips 451 VGA BIOS 2.0.1, valid checksum.

- [MB007 286 system BIOS Low / High pair](unknown/mb007-286-bios/) — two matching
  32 KiB reads per chip; reconstructed 64 KiB Phoenix 3.10 / CEC286 02.04 BIOS.

- [VID004 ASUS GMIO-470 VGA BIOS v1.1](asus/vid004-gmio470-v11/) — two matching
  32 KiB reads, valid VGA checksum; matching 64 KiB probes retained, chip type unresolved.

- [VID003 Hercules Stingray VL BIOS 1.04.A](hercules/vid003-stingray-vl-104a/) —
  two matching 32 KiB T48 reads; valid VGA checksum, provisional 27256 type.

- [VID002 Phoenix S3 86C801/805 GENDAC BIOS 2.13.063F03](s3/vid002-phoenix-213063f03/) —
  two matching 32 KiB 27256 reads; valid VGA option-ROM checksum.

- [VID001 Phoenix S3 86C801/805 GENDAC BIOS 2.13.065](s3/vid001-phoenix-213065/) —
  two matching 32 KiB 27C256 reads; valid VGA option-ROM checksum.

- [MB005 LC-2516 / LC-2517 BIOS pair](unknown/mb005-lc2516/) — two matching
  32 KiB reads per chip; reconstructed 64 KiB Acer/Investronica 8086 XT-plus
  BIOS 2.01B with zero byte sum. Related public dump awaits binary comparison.

- [GW-VGA Chips 451 BIOS v2.1.0](chips/gw-vga-451-v210/) — two matching
  32 KiB T48 reads, valid option-ROM checksum; 64 KiB probe repeats the image.
  Physical EPROM type provisional; no match in three related 86Box candidates.

- [Probable Nokia MAC4-family firmware, MAC 3.04](unknown/satellite-mac304-m27c2001/) —
  two matching 256 KiB M27C2001 reads; banked 8051 firmware dated 1993-10-13.
  [Investigation](unknown/satellite-mac304-m27c2001/analysis/) includes ten-language
  resource catalogs, hidden service menus and a reproducible emulator harness.
  Exact receiver model remains unconfirmed.

- [Edimax ISA-16 boot ROM V3.2](edimax/isa16-v32/) — two matching 8 KiB
  2764 reads, valid PC option-ROM checksum; Novell NetWare V2.10 loader,
  Edimax version dated 931201. No exact public match found.

- [EFA IES16 Novell RPL boot ROM](efa/ies16-rpl-v100/) — two matching 8 KiB
  2764 reads, valid option-ROM checksum; RPL v1.00 (920626),
  EFA NE2000-compatible MLID v1.0B (940331). No exact public match found.

- [D-Link NE2000 BootROM V2.40](d-link/ne2000-v240/) — two matching 8 KiB
  2764 reads; Novell NetWare remote DOS loader, valid PC option-ROM checksum
  and emulator-verified INT 19h installer. No exact public match found.

- [Puritan Bennett 7200 MEGACPU](puritan-bennett/7200/megacpu/) — all eight available chips (0–6, 8),
  two matching 64 KiB T48 reads each; x86 boot diagnostics and 26300-85-V text;
  provisional device type. Acquisition complete for present chips; chip 7 missing.

- [Puritan Bennett 7200 display controller](puritan-bennett/7200/display-controller/) —
  Q1 oxygen-flow, Q2 air-flow and Q3 exhalation sensor EPROMs, two matching T48
  reads each; duplicated 2 KiB images with matching embedded sensor identifiers. Physical chip type remains provisional.

- [`Kaypro 2 PC003 character ROM, 81-233A`](kaypro/pc003-81-233a-chargen/) —
  two matching 2 KiB T48 reads; accented Latin alternate glyphs. Includes an
  atlas, pixel-difference visualizations and reproducible analysis against 81-146A.

- [Perkin-Elmer TAC7/DX U35/U36](perkin-elmer/tac7dx/) — two matching T48
  reads per chip as 27256; U35 has identical 16 KiB halves, U36 has distinct
  halves. Raw 32 KiB captures retained; exact chip types remain provisional.
  Includes [6809 firmware analysis and execution](perkin-elmer/tac7dx/analysis/):
  embedded checksums, synthetic boot, 64 command cases and an acquisition IRQ.

- [`Unidentified U2716C35`](unknown/u2716c35-20261110/) — two matching
  2 KiB reads using different address shifters; Z80 keyboard-handling component
  linked at 6800h, with emulator-verified 12 × 8 scan and 64-byte event queue.
  Possibly Robotron according to the owner; exact system unknown. All address bits
  distinguish data, unlike the RF2 diagnostic candidates.

- [`Robotron PC1715 MB002, originally MB001`](robotron/pc1715-mb002/) —
  U2716C35 A25.3, known S502 with two matching reads; owner-reported boot issue
  before a ROM swap is not explained by content corruption.

- [`Robotron PC1715 PC002`](robotron/pc1715-pc002/) — known S502 boot and S619/S605 character ROMs;
  two matching reads each. Boot matches MB001; A25.2 character ROM differs.

- [`Robotron PC1715 MB001`](robotron/pc1715-mb001/) — known S502 boot and S643/S605 character ROMs;
  each acquired with two matching reads and identified by reference hashes.

- [`Robotron PC1715 S642 QWERTY/ЯВЕРТЫ keyboard`](robotron/pc1715-keyboard-s642-qwerty/) —
  two matching 2 KiB reads; differs from JCUKEN S642 only in keycode tables.
  Matrix/modifier, alphabet and automated TOS/M end-to-end tests pass.

- [`Robotron PC1715 S642 keyboard`](robotron/pc1715-keyboard-s642/) —
  repeat-read 2 KiB dual-language firmware; MAME matrix, modifier and
  persistent language-toggle tests pass.

- [`Landis & Gyr UNIGYR PRU_AC`](landis-gyr/pru-ac-20260924/) — six-chip
  set, likely a PAA1 program card for PRU1. 68HC11 firmware dated 1993-11-04;
  recovered bank map and passing original ROM checksum. Four EEPROMs include
  Estonian/Finnish configuration text; chip 2's repeated-page capture remains
  unverified. [Deep analysis and CPU survey](landis-gyr/pru-ac-20260924/analysis/).
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

- [MBI XT / Phoenix 2.27 BIOS](unknown/mbi-xt-phoenix-227/) — three matching
  8 KiB 2764 reads; suspect zero byte in BIOS banner and nonzero checksum.
  Raw image preserved; separate one-byte correction passes 86Box POST, DOS boot
  and BIOS service checks.

- [RF5 recheck and CPU survey](unknown/rf5-plastic-20260920-recheck/) —
  two matching nonblank reads; identity unresolved.
- [Programmer-output echo model](analysis/20260919-programmer-echo/) and
  [27256 CE-state audit](analysis/20260920-27256-ce-audit/) — distinguish
  anomalous captures from chip contents and document the reader correction.
- [Third 27256](unknown/27256-20260920-chip03/) — single FF/F7-only capture;
  stored-data validity remains unresolved.
- [Blank 27256 read records](analysis/20260921-27256-blank-records/) —
  metadata only; all-FF binaries are excluded.

- [Norma Systems VMD-4 v1.1](norma-systems/vmd-4/27c512/) — 64 KiB 27C512 capture, firmware 1.01, single read.
