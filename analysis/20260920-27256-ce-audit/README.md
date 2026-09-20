# 27256 audit: confirmed reader CE-state bug

On 2026-09-20 the owner requested an Internet, jumper and code audit after
two different 27256 chips produced the same output-echo signature. The audit
identified a concrete defect in the R27256 command added earlier in this
session. No hardware operation was performed during this audit.

## Source evidence

The pinned [Geepro 27xx implementation](https://github.com/danielg4/geepro/blob/a08efcaf6479730d552c5f96bad0a2a01bf0635f/chips/27xx.cpp)
registers reads of 2764/27128 with CE parameter **1**, and 27256 with **0**.
The [module macro](https://github.com/danielg4/geepro/blob/a08efcaf6479730d552c5f96bad0a2a01bf0635f/chips/modules.h)
passes that parameter through `start_action` to `hw_set_ce`. The
[Willem driver](https://github.com/danielg4/geepro/blob/a08efcaf6479730d552c5f96bad0a2a01bf0635f/drivers/willem.cpp)
uses DB25 pin17 for CE/PGM according to physical routing.

Our R27256 v1 selected `wl_begin_2764_read`, driving that line high. It
should select a startup with the line low. The corrected local reader has a
separate `wl_begin_27256_read` entry point using the same startup levels as
2716, while retaining 27256 capacity and physical routing.

The [Geepro jumper template](https://github.com/danielg4/geepro/blob/a08efcaf6479730d552c5f96bad0a2a01bf0635f/drivers/willem.xml.in)
confirms DIP1B3, ON 1,2,5,6,8,9, for 27256. There is no evidence from this
audit that the owner set those switches incorrectly. Keep Normal 28-pin
routing and the established PCB3B compatibility selector position.

The manufacturer's [ST M27C256B datasheet](https://www.mouser.com/datasheet/2/389/stmicroelectronics_cd00000515-1204492.pdf)
requires active-low E and G for reading; E high disables output. Read-mode
VPP is VCC, which differs from enabling the programmer's high-voltage VPP
switch. The exact full marking of the owner's chips is still unknown.

## Why this fits the captures

Incorrect CE can leave the EPROM output undriven. The observed data match
our previously documented programmer-output echo model byte for byte.
A software error repeated for every R27256 invocation explains why changing
chips and power cycling did not change the output. It is the leading
explanation, but successful corrected hardware reads remain the confirmation.

RF5 already used the correct low CE/PGM state, so this newly identified
R27256 bug does **not** explain the earlier RF5 echo. Different faults can
produce the same readback symptom. Its later non-echo captures do not validate
the old R27256 command.

The initial virtual test modeled address range and serial data, but returned
ROM data regardless of 27256 CE. That omission let the incorrect startup pass.
The revised model honors 27256 CE, explicitly tests VCC/CE/VPP state, checks
all 32768 addresses and rejects the original startup. A mutation test restoring
the old behavior fails with `27256 must hold CE low and VPP off`.

## Internet symptom reports

A [firsthand PCB5.0E report from 2013](https://forum.allaboutcircuits.com/threads/need-help-with-willem-eprom-pcb-5-0e.81003/)
shows long runs of 04/06 (and 14/16) while attempting several EPROM types.
It is similar, not an exact copy of our sequence; that thread does not show a
confirmed root cause. Suggestions about power, software mode and timing are
not proof that those are our fault.

A [separate firsthand Willem report](https://www.circuitsonline.net/forum/view/76936)
describes reversed DIP ON/OFF interpretation causing incorrect 2764/27256
reads and says correcting the switches fixed that owner's problem. This
shows settings can produce bad reads, not that our user's switches are wrong.
Our specific source-code mismatch is stronger evidence in this case.

## State after the audit

Corrected local build: `dosravi-27256-ce-fix-v2`.
The previous binary on the Pocket8086 remains unchanged; upload and verify the
corrected executable before the next owner-authorized read. No further read,
serial operation, programming, or jumper change was performed during the audit.
The old raw captures remain preserved as diagnostic evidence.

All portable tests and the complete DOSBox-X 8086/80186 matrices passed.
Build identity and validation status are recorded in `build.json`.

## First physical test of the fix

The corrected binary was subsequently uploaded as `RD256V2.COM`, with CRC
verified, and run on the same installed second 27256 after owner authorization.
The result changed from the echo pattern to all FF. This supports the CE
diagnosis, but does not yet validate known programmed contents or all address
lines. No all-FF binary was added to the dumps repository. See `build.json`.
