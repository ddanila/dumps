# Cirrus Logic GD-5422 VGA BIOS — 27512 capture

The owner described this chip as a **27512, AWARD 486DX BIOS**. The captured
contents instead identify a **Cirrus Logic GD-5422 VGA option ROM**:

- `CL-GD540X/542X VGA BIOS Version 1.00d`
- `5422 08/07/92` (date reproduced as stored)
- `Cirrus Logic GD-5422 VGA`
- Cirrus Logic 1992 and Quadtel 1987–1990 copyright strings.

The full 65,536-byte read is preserved as `read1.bin`. Bytes 0000h–7FFFh
contain a 32 KiB option ROM: signature `55 AA`, size byte `40`, and an
8-bit additive checksum of zero over the declared image. Bytes 8000h–FFFFh
are entirely `00`. The halves are different. These checks support a plausible
capture, but do not independently establish the physical chip's capacity or
repeatability. This was one authorized read; no second read was performed.
No motherboard or graphics-card model has been established.

Read on 2026-09-21 with Willem PCB5.0E, Pocket8086 LPT378, DOSRAVI at 57600,
and the new `dosravi-27512-read-v1` reader uploaded as `RD512V1.COM`.
The supplied setup was Normal 28-pin routing, DIP1D4 (ON 3,5,7,8,9), 5 V VCC,
software VPP off, and two empty ZIF rows at the lever. The owner requested
reading after these instructions; no fresh rail measurement was made.

Command: `RD512V1.COM R27512 AW486A.BIN 378 /PROFILE:conservative`.
Execution 2390451112 exited zero; scan including chunk I/O took 901395 ms.
The reader reported VCC and VPP off at completion. Host CRC16-CCITT `39AF`
matches the DOS result. See `manifest.json`, `SHA256SUMS`, and `analysis.json`.

Reader validation passed the portable tests, the DOSBox 8086/80186 matrices
(including full 64 KiB output and CRC), and an A15 alias mutation test.
`evidence/reader-build.json` and `reader-source.patch` identify the build;
the original executable and full serial evidence remain in the DOSRAVI
session `27512-award486-20260921-read1`. `WILLEM.LOG` may include previous
runs, and its DOS date is incorrect; the acquisition date uses the host.

The capture was acquired before the reader changes were committed; the
archived build metadata and source patch record that acquisition-time state.

Reader implementation: [willem-v30 commit e12094e](https://github.com/ddanila/willem-v30/commit/e12094e).
