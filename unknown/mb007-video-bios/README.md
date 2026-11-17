# MB007 — integrated video BIOS, Low chip

Source: MB007, a 286 mainboard with integrated video, per owner. Physical video
chipset and full EPROM markings remain unrecorded. This is separate from the
[system BIOS pair](../mb007-286-bios/).

## Acquisition — 2026-11-17

Owner identifies the chip as **27128, Low**. Two independent read-only T48
captures using `M27128A@DIP28`, with chip-ID probing skipped, produced identical
16,384-byte images. No programming or byte repairs were performed.

[Untouched Low dump](mb007-video-bios-low.bin)

- SHA-256: `d34ca970f6778a13c64129ca745e096f485ea59f9e52ef1b250971c4cbf86164`
- CRC32: `1870d66f`
- Byte sum modulo 256: `2E`

The text contains alternating-character fragments consistent with one byte lane
of a paired video BIOS. High has not yet been acquired. This chip's nonzero sum
is not evidence of corruption: the complete option-ROM checksum requires the
reconstructed image. Firmware identification and boot testing remain pending.

No match was found among 1,235 eligible 16–256 KiB files in the local 86Box ROM
collection, checking contiguous data and extracted even/odd byte lanes. Public
comparison should be revisited after acquiring High; uniqueness is not established.

[Acquisition evidence](evidence/low/) · [Manifest](manifest.json)

[Inventory record](https://github.com/ddanila/vintage-computer-inventory/tree/main/items/MB007-286-integrated-video)
