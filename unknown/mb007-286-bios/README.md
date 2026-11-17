# MB007 — 286 system BIOS, Low chip

Source: MB007, a 286 mainboard with integrated video, per owner. Manufacturer,
model, PCB revision, serial number and chip label are not yet recorded.

## Acquisition — 2026-11-17

Owner identifies the first system BIOS chip as **27256, Low**. Two independent
T48 reads using `M27256@DIP28`, with chip-ID probing skipped, yielded identical
32,768-byte images. No programming was performed. The untouched first read is
[`mb007-system-bios-low.bin`](mb007-system-bios-low.bin).

- SHA-256: `640d2dafe5c861ab34848a75a1163d6cdc5f25ce97f996efda85e5b5e3b52f95`
- CRC32: `fdf30486`
- Byte sum modulo 256: `00` (this chip alone; not validation of the complete BIOS)

The image contains `Copyright 1985-1988 Phoenix Technologies Ltd.` and
alternating-character text consistent with a byte lane of a paired BIOS.
The High chip has not yet been acquired. Complete BIOS version, reconstruction,
checksum validation and boot testing remain pending. No bytes were repaired.

No match was found in 1,113 eligible 32–256 KiB files in the local 86Box ROM
collection, including contiguous data and extracted even/odd byte lanes.
Public identification/comparison should be revisited after acquiring High;
absence of a local match does not establish uniqueness.

[Read logs and analysis](evidence/low/) · [Manifest](manifest.json)

[Inventory record](https://github.com/ddanila/vintage-computer-inventory/tree/main/items/MB007-286-integrated-video)
