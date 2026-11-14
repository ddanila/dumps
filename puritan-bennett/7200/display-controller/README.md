# Puritan Bennett 7200 display controller sensor EPROMs

Board photographed by owner: Display Controller Assy 19570, revision label
`-30D`. The three yellow-labelled EPROMs are Q1/U406, Q2/U504 and Q3/U507.
All three have been acquired with two matching reads per chip. Photo reference:
`/home/ddanila/Downloads/133870084.jpg`.

## Q1 / U406: Q1-962269, 19536-H

Read twice on 2026-11-14 using T48 firmware 00.1.03 and minipro 0.7.4:

```sh
minipro -p M2732A@DIP24 -x -r OUTPUT.bin
```

Both reads exited zero and match byte for byte. ID probing was disabled;
no programming or erase command was issued. The profile specifies 5 V for
read/verify; no independent chip-rail measurement was made. Minipro warns
about incomplete T48 support and older-than-expected programmer firmware.

The preserved raw capture is 4096 bytes, with identical 2048-byte halves.
Each half has 252 distinct byte values and contains the ASCII identifier
`Q1-962269` at offset 0x7f5, matching the physical sticker. CRC32 of the
full capture is `e2f5f5ba`. The original duplicated bytes are retained.

This supports a 2 KiB image, but does not prove physical chip type or capacity.
The owner reports 24 pins and a partly visible `27` marking. A standard 2716
requires pin 21 (VPP) high during reads; the 2732 profile drives it as A11.
Thus the upper 2 KiB is the candidate image with the appropriate pin-21
level if this is a standard 2716. Here the lower half happens to match.

## Content

The body contains increasing little-endian 16-bit values, consistent with
sensor calibration lookup data. The first two words are 1006 and 1122;
the following table rises from zero to 4521, followed by FF padding, the
sensor identifier and two trailing bytes. Field meanings, scaling and any
checksum interpretation have not been established. This is not yet decoded
as executable firmware.

The manufacturer's [parts list](https://doczz.net/doc/2483138/puritan-bennett-7200)
identifies 19536 as the oxygen flow sensor supplied with an EPROM, 19535 as
the air flow sensor, and 18256 as the exhalation sensor. This supports the
sensor-calibration interpretation; the matching embedded serial number
further ties this capture to the photographed Q1 chip.

Public searches by sticker, candidate-image SHA-256 and system name found
no downloadable matching dump. This does not establish Internet uniqueness.
Original logs and session metadata are preserved in `evidence/`; both raw
reads remain in the local session path recorded in `manifest.json`.

## Q2 / U504: Q2-962379, 19535-H

Read twice on 2026-11-14 with the same T48 and provisional `M2732A@DIP24`
profile, with ID probing disabled. Both reads exited zero and match exactly.
The 4096-byte raw capture contains identical 2048-byte halves, each with
254 distinct byte values. Its CRC32 is `3e4746fc`. As for Q1, repetition
supports a 2 KiB image but does not prove the physical device type.

The identifier `Q2-962379` occurs at offset 0x7f5 in each half and matches
the sticker. The body contains increasing little-endian 16-bit values,
consistent with air-flow sensor calibration data. The table differs from Q1;
its values after the first two words rise from zero to 5449 before FF
padding, the identifier and two trailing bytes. Units and checksum meaning
remain unconfirmed. The full duplicated capture is retained unchanged.

Searches by Q2 label and candidate-image hash found no matching downloadable
candidate. Original read logs and session metadata are in `evidence/`.

## Q3 / U507: Q3-963423, 18256-E

Read twice on 2026-11-14 using the same T48 and provisional `M2732A@DIP24`
profile, with ID probing disabled. Both reads exited zero and match exactly.
The 4096-byte capture contains identical 2048-byte halves, each with 253
distinct byte values. CRC32 of the raw capture is `ed178012`. The physical
chip type remains unconfirmed; the full duplicated capture is preserved.

Each half contains `Q3-963423` at offset 0x7f5, matching the sticker. The
little-endian 16-bit table following the first two words rises from zero
to 6001 before FF padding, the identifier and two trailing bytes. This is
consistent with the exhalation-flow sensor calibration interpretation.
Physical units and any checksum interpretation remain unresolved.

Public searches by Q3 label and candidate-image hash found no matching
downloadable candidate. Both original read logs and metadata are preserved
in `evidence/`; the complete two-read session remains at the recorded path.

All three captured images have the same broad layout but different numeric
tables and matching individual sensor identifiers. All three yellow-labelled
sensor EPROMs on this display controller are now preserved.
