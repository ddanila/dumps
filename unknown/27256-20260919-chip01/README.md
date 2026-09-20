# 27256-class chip: anomalous capture, 2026-09-19

The owner identified this as a 27256-class chip and confirmed jumper setup
and insertion. Full markings and provenance have not been provided.

The newly added `R27256` command read 32,768 bytes using conservative timing.
The scan took 448.250 seconds, returned zero, and reported VCC/VPP safely off.
The host and uploaded executable CRC32 matched. Virtual-board tests checked
all addresses including A13/A14; the DOSBox 8086 and 80186 test matrices passed,
including exact 32 KiB output and CRC. This establishes software test coverage,
not successful physical ROM acquisition.

The capture has `00` at address zero, `06` at every odd address, and `04` at
all other even addresses. Its first 2 KiB exactly match the preceding
[plastic РФ5 capture](../rf5-plastic-20260919/README.md). The same anomalous
pattern on different chips and routing settings suggests a shared read-path
fault; actual chip contents remain unknown. No recognizable firmware was
recovered. A second read was skipped in favor of checking the hardware path
with a known-programmed control. No programming or erasure was performed.

The raw capture is retained as diagnostic evidence. Original DOS stdout,
logs, and execution/session records are in `evidence/`; the complete serial
transcript remains in the DOSRAVI session identified in `manifest.json`.
WILLEM.LOG is cumulative and can include previous operations. DOS timestamps
are not the acquisition date.

A later [known EktaSoft AT28C64 control](../../juku/ekta37-low-control-20260919/)
passed two exact 8 KiB comparisons after changing to its DIP12B setup.
That validates the later AT28C64 configuration, but does not resolve this
capture or prove this chip faulty.

[Offline protocol analysis](../../analysis/20260919-programmer-echo/README.md)
reproduces every byte with a programmer-output echo model, including the
initial `00`. The exact physical cause remains unconfirmed.

## Recheck on 2026-09-20

After the RF5 produced two matching non-echo captures and the owner changed
to the confirmed 27256 settings, another conservative 32 KiB read returned
exactly the same bytes as this original capture: CRC16 `5DFA`, initial `00`,
then alternating `06`/`04`. The command returned zero, took 448.195 seconds
for scanning, and reported safe VCC/VPP shutdown. Evidence is retained under
`evidence/recheck-20260920/`; the unchanged binary is not duplicated. Actual
27256 contents remain unknown, and this is still not a verified ROM image.

## Power-cycle recheck on 2026-09-20

The owner power-cycled the Willem and requested another read with unchanged
settings. All 32768 bytes again matched the original echo capture exactly
(CRC16 `5DFA`). The scan took 448.250 seconds, returned zero and reported safe
VCC/VPP shutdown. Power cycling did not resolve the symptom. Evidence is in
`evidence/powercycle-20260920/`; the unchanged binary is not duplicated.

## Reader defect identified

The [2026-09-20 code audit](../../analysis/20260920-27256-ce-audit/README.md)
found that R27256 v1 incorrectly used the 2764 high CE/PGM state, instead of
the required low state. This is the leading explanation for these captures.
The local correction is awaiting upload and a new authorized physical read.
