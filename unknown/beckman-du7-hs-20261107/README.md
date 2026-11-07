# Unknown 8088 board: provisional Beckman DU-7 HS identification

Acquired 2026-11-07. Owner reports an 8088 CPU and eight ROM chips.
Chip 2 contains “Beckman Instruments” and “DU-7 HS Operating Instructions”;
this is an identification clue, not independently confirmed board provenance.

The owner clarified that numbers 1–8 denote onboard positions **U101–U108**.
The chips may have been moved/reseated before acquisition. Preserve these
observed positions separately from any subsequently inferred firmware order.
The mixed 2732/2764 placement is owner-reported; it does not establish a
socket-order error. Earlier session notes saying socket order was unknown
predate this clarification. No chips were rearranged by the acquisition software.

| Owner number | Board position | Reported chip | Bytes | CRC32 | Verification |
| --- | --- | --- | ---: | --- | --- |
| 1 | U101 | 2732 | 4096 | `132b4e25` | Single capture; repeatability unchecked |
| 2 | U102 | 2764 | 8192 | `f8317894` | Single capture; repeatability unchecked |
| 3 | U103 | 2732 | 4096 | `fded19b7` | Single capture; repeatability unchecked |
| 4 | U104 | 2732 | 4096 | `608ac1fe` | Anomalous alternating 06/04; second read identical |
| 5 | U105 | 2732 | 4096 | `b78ac525` | Single capture; repeatability unchecked |
| 6 | U106 | 2732 | 4096 | `2afe0c12` | Single capture; repeatability unchecked |
| 7 | U107 | 2732 | 4096 | `a9e1ea08` | Single capture; repeatability unchecked |
| 8 | U108 | 2764 | 8192 | `e82ae93c` | Single capture; repeatability unchecked |

Physical setup: Willem PCB5.0E, Pocket8086 LPT 378h, CP2102 serial at
57600 baud. 2732 uses special routing/DIP1C0; 2764 uses Normal routing/DIP12B.
Reader: `RD32V1.COM`, build `dosravi-2732-read-v1`, SHA256
`eece740b613644a470712eb1d550aafe45875ac9d3cf13b4ebbca4f87a9a8969`.
All commands exited zero and logged VCC off/VPP off. This reports software
shutdown, not a meter measurement. Host date is authoritative; DOS clock is 1980.

Chip 4 has initial 00, followed by alternating 06/04; both captures match.
This is suspicious and is not accepted as confirmed firmware. All binaries
and original evidence remain in local DOSRAVI sessions, including chip04-read2.
Firmware is not added here pending verification and public-collection comparison.
`manifest.json` records local evidence locations and capture hashes.
