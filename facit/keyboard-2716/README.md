# FACIT terminal keyboard ROM

24-pin ROM from a FACIT terminal keyboard using an Intel 8035, as reported by the owner. The keyboard has English and Russian layouts. The ROM sticker identifies it as `4431 KBCL`, `LAT/CYR`, `6800 U3`, consistent with a FACIT 4431 keyboard. The underlying chip type remains unconfirmed; manufacturer markings remain covered by the preserved sticker. Read using the standard 2716-compatible profile. This 2 KiB capture does not establish the chip's full physical capacity.

## Owner-reported identification

- Keyboard layouts: English and Russian.
- ROM sticker text, transcribed by the owner: `4431 KBCL, LAT/CYR. 6800 U3`
- Sticker line breaks were not specified. `6800 U3` is recorded as label text without interpreting it as a processor type or board position.

## Acquisition

See [quick analysis and 8035 emulation](ANALYSIS.md) for the ROM checksum,
code structure, and successful Latin/alternate-table keyboard tests in MAME.

- Host date: 2026-09-17. DOS clock timestamps are not acquisition dates.
- Programmer: user's 2015 Willem PCB5.0E; Pocket8086 LPT 378h.
- Transport: DOSRAVI 0.1.1, CP2102 serial at 57,600 baud.
- Reader: existing willem-v30 build uploaded as RD2716.COM.
- Command: `RD2716.COM RRF5 FACIT1.BIN 378 /PROFILE:conservative`, repeated with FACIT2.BIN.
- Expected physical setup: special 2716 J1/J2 routing, J9/J10 toward DB25, DIP ON 1/2/6/8/9, 5 V VCC, bottom-aligned 24-pin chip. Physical settings and voltages were not independently measured in this session.
- Two independent reads match byte-for-byte: 2,048 bytes, 28,050 ms and 27,995 ms respectively. Both returned zero and reported safe shutdown with VCC/VPP off. Software VPP stayed disabled.
- Non-uniform data: 246 distinct byte values; all eight 256-byte pages are distinct.
- CRC32: `7AB50D44`
- SHA-256: `9e99be945655d39d9fbb34a32ec66969612442eda4f1e6992a43e454991a2034`

Reader output, logs, execution identities, and session metadata are retained in `evidence/`. Full serial transport records remain in `/home/ddanila/fun/dosravi/sessions/facit-keyboard-20260917-read1` and `facit-keyboard-20260917-read2`.

The retained `WILLEM.LOG` files are unmodified cumulative programmer logs
and include earlier operations. The final run in each log is the corresponding
FACIT acquisition; `read1-STDOUT.TXT` and `read2-STDOUT.TXT` contain only the
individual read's output. `manifest.json` records the ROM and reader identity.
