# Third loose 27256 — 2026-09-20

One read with corrected reader `dosravi-27256-ce-fix-v2` produced 32,768 bytes:
31,952 `FF` and 816 `F7`. Only data bit D3 differs from the erased value.
Non-FF bytes occur from `0x0000` through `0x2601`.
No printable ASCII strings of six or more characters were found.
This is not the earlier `00/06/04` programmer-output echo.

The capture is not fully blank. Incomplete erasure, stored/test data, or a
read-path/chip issue remain possibilities; a single read does not resolve them.
No repeat read was requested or performed. Full chip markings and provenance
are unknown; the owner identified this as another 27256.

Used Willem PCB5.0E, Pocket8086 LPT 378h, Normal J1/J2 routing, DIP 1B3,
unchanged settings confirmed by the owner. Command:
`RD256V2.COM R27256 E25603A.BIN 378 /PROFILE:conservative`.
Read took 448855 ms; exit code 0; safe shutdown reported VCC and VPP off.

`read1.bin` preserves the original bytes. See `manifest.json` and `SHA256SUMS`
for checksums and acquisition details. Original stdout and logs are in
`evidence/`; `WILLEM.LOG` can include prior runs. The DOS clock is incorrect;
the acquisition date uses the host clock. Full transport evidence remains in
`/home/ddanila/fun/dosravi/sessions/27256-20260920-chip03-read1`.
