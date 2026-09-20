# EktaSoft 3.7 low EEPROM: known-content control

Read on 2026-09-19 from the owner's AT28C64-class chip carrying the EktaSoft
3.7 low (D15) image. Exact package markings were not supplied. This is a
programmed replacement/control chip, not a newly identified original ROM.

Two independent conservative reads match each other and all 8,192 bytes of
`8080-cosim/ref/eprom-images/d15_ekta37_low.bin` exactly. CRC16-CCITT is `060D`;
SHA-256 is `d6c4ec7418f05e5761ef450e6ee36fb2579d65d9cbf87dce265eaf1c0d077596`.
Both commands returned zero and reported VCC and VPP safely off. No write
command was used. Setup, executable identity, timings and execution IDs are
recorded in `manifest.json`; original evidence is retained under `evidence/`.
DOS timestamps are not the acquisition date.

This confirms the current AT28C64 read setup works. It does not validate
previous all-FF captures, the special 2716 route, or the 27256 A13/A14 routing.
The earlier [RF5](../../unknown/rf5-plastic-20260919/) and
[27256](../../unknown/27256-20260919-chip01/) anomalous patterns remain
unresolved. Setup/contact issues or chip faults still need to be distinguished.
