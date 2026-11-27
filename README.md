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

Layout, README and manifest conventions are in [CONTRIBUTING.md](CONTRIBUTING.md).
Run `python3 tools/check.py` before committing; CI runs it on every push.

## Sets

Each set's README gives the chip markings, where the chips sat on the board,
acquisition details, checksums and open questions.

### Computers and terminals

- [Robotron PC1715](robotron/pc1715/): boot and character ROMs from three
  machines (MB001, MB002, PC002) and two S642 keyboard variants (JCUKEN and
  QWERTY/ЯВЕРТЫ). The keyboard firmware passes matrix, modifier and
  language-toggle tests in MAME.
- [Kaypro 2 PC003 character ROM 81-233A](kaypro/pc003-81-233a-chargen/):
  accented Latin alternate glyphs, compared against 81-146A.
- [FACIT 4431 LAT/CYR keyboard](facit/keyboard-2716/): Intel 8035 firmware;
  MAME confirms matrix scanning and serial key output.
- [Estafeta-03](estafeta-03/tms2764-lhp8749/): 8086-compatible code with an
  `ЭСТАФЕТА - III` banner; board and revision unconfirmed.

### PC BIOS and expansion-card ROMs

- [ASUS GMIO-470 VGA BIOS v1.1](asus/gmio470-v11/)
- [Hercules Stingray VL BIOS 1.04.A](hercules/stingray-vl-104a/)
- [Phoenix S3 86C801/805 GENDAC BIOS 2.13.063F03](s3/phoenix-gendac-213063f03/)
  and [2.13.065](s3/phoenix-gendac-213065/)
- [GW-VGA Chips 451 BIOS v2.1.0](chips/gw-vga-451-v210/)
- [Edimax ISA-16 boot ROM V3.2](edimax/isa16-v32/): Novell NetWare V2.10 loader
- [EFA IES16 Novell RPL boot ROM](efa/ies16-rpl-v100/): RPL v1.00 with
  NE2000-compatible MLID
- [D-Link NE2000 BootROM V2.40](d-link/ne2000-v240/): NetWare remote DOS
  loader; INT 19h installer verified in an emulator

### Modems and telecom

- [Nokia Data Modem 2400/2400](nokia/data-modem-2400-2400/): 8031 controller,
  Am2901 bit-slice microcode and a sine/lookup PROM. The
  [investigation](nokia/data-modem-2400-2400/analysis/) points to a V.26 ter-class
  duplex modem.
- [Probable Nokia MAC4-family satellite receiver, MAC 3.04](unknown/satellite-mac304-m27c2001/):
  banked 8051 firmware dated 1993-10-13, with ten-language resources, hidden
  service menus and an emulator harness. Exact model unconfirmed.

### Instruments and industrial

- [Puritan Bennett 7200 ventilator](puritan-bennett/7200/):
  [MEGACPU](puritan-bennett/7200/megacpu/) x86 boot diagnostics (chip 7 missing)
  and [display-controller](puritan-bennett/7200/display-controller/) flow-sensor
  EPROMs.
- [Perkin-Elmer TAC7/DX](perkin-elmer/tac7dx/): 6809 firmware with
  [analysis and execution](perkin-elmer/tac7dx/analysis/), covering checksums,
  boot and 64 command cases.
- [Landis & Gyr UNIGYR PRU_AC](landis-gyr/unigyr-pru-ac/): 68HC11 program
  card firmware dated 1993-11-04, with Estonian/Finnish configuration EEPROMs
  and [deep analysis](landis-gyr/unigyr-pru-ac/analysis/).
- [Diversa Aquarius 2000 Q-meter](diversa/aquarius-2000/)
- [Norma Systems VMD-4 v1.1](norma-systems/vmd-4/27c512/): firmware 1.01.

### Unidentified

- [Mitsubishi M5L27128K](unknown/mitsubishi-m5l27128k/): unidentified contents queued
  for future analysis; metadata only, binary retained in the local acquisition session.

- [Intel D27010](unknown/intel-d27010/): unidentified contents queued for future
  analysis; metadata only, binary retained in the local acquisition session.
- [Tandberg TDV-2200S-family TMM27128AD-20](unknown/tandberg-tdv2200s-tmm27128ad/):
  8085 terminal services and partial application, with 80 × 25 display, serial
  I/O and programmable PUSH keys; exact model/revision unresolved.
- [MB007 286 mainboard](unknown/mb007/): Phoenix 3.10 / CEC286 02.04
  [system BIOS](unknown/mb007/system-bios/) and Chips 451
  [video BIOS](unknown/mb007/video-bios/).
- [MB005 LC-2516 / LC-2517](unknown/mb005-lc2516/): Acer/Investronica 8086
  XT-plus BIOS 2.01B.
- [Award VENUS-VIA 1993-04-14](unknown/award-venus-via-19930414/): Award 4.20
  BIOS with Cirrus VGA.
- [U2716C35](unknown/u2716c35-z80-keyboard/): Z80 keyboard-handling code, possibly
  Robotron.
- [K573RF5 set 41-44](unknown/k573rf5-set-41-44/): 8080-compatible
  instrumentation firmware with a GPIB-style interface.

## Rights

No license is asserted over the dumped firmware images. They may contain
copyrighted software belonging to unidentified rights holders. Metadata and
checksums are supplied for identification, preservation, and research.

## Acquisition investigations

Records of problem reads, reader corrections and captures that are not (yet)
trustworthy firmware.

- [MBI XT / Phoenix 2.27 BIOS](unknown/mbi-xt-phoenix-227/): suspect zero byte
  in the BIOS banner. A separate one-byte correction passes 86Box POST, DOS boot
  and BIOS service checks; the raw image is preserved.
- [RF5 recheck and CPU survey](unknown/rf5-plastic-recheck/): identity
  unresolved.
- [Programmer-output echo model](analysis/20260919-programmer-echo/) and
  [27256 CE-state audit](analysis/20260920-27256-ce-audit/): tell reader
  artefacts apart from chip contents and document the reader fix.
- [Third 27256](unknown/27256-chip03/): FF/F7-only capture; validity
  unresolved.
- [Blank 27256 read records](analysis/20260921-27256-blank-records/): metadata
  only; all-FF binaries are excluded.
- [Probable Beckman DU-7 HS](unknown/beckman-du7-hs/): inventory and
  analysis of eight ROMs from an 8088 board. The binaries stay in local
  sessions until one suspicious chip is re-verified.
- [Norma Systems VMD-4 AT29C512](norma-systems/vmd-4/at29c512/): anomalous first
  capture.
