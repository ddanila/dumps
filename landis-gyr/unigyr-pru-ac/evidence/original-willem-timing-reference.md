# Original Willem timing references (2026-09-24)

An old GQ-3X sales comparison explicitly separates parallel-port Willem read
times from USB read times and write times:

| Chip | Size | Parallel Willem read |
|---|---:|---:|
| AT29C040A | 512 KiB | 101 seconds |
| M29F040B | 512 KiB | 69 seconds |
| AM29LV320 | 4 MiB | 570 seconds |

Source: https://www.easytechnology.gr/electronics/programmers/true-usb-willem-programmer-gq-3x-prg-028-willem-full-pack?language=en

These are vendor-published comparisons, not measurements on our hardware.
Host, software version, and exact parallel programmer revision are unspecified.
Scaling the first two linearly gives 17–25 seconds for 128 KiB: an illustrative
desktop-PC baseline only, not a prediction for Pocket8086 or M27C1001.

Primary firsthand investigation by PY2BBS, dated 2006-10-29:
https://www.py2bbs.qsl.br/download/willem_pcb3b_to_pcb45.pdf
Pages 15–16 (PDF indexes 14–15) benchmark AM29F040B *programming plus verification*,
not read-only: Pentium 233MMX/Windows ME 1079s PCB3B, 392s PCB4.5;
Athlon XP 2400+/Windows 2000 420s PCB3B, 198s PCB4.5.
The same report explains PCB4.5 shifts three address lanes in parallel,
requiring eight clocks, and reads several data bits per status sample.
Our existing setup remains PCB3B, with the tested serial address/data paths.

Do not confuse GQ true-USB timing figures with LPT Willem timings. No exact
original-software M27C1001 read benchmark on a matching host was found.
