# VID002 — Phoenix S3 86C801/805 GENDAC BIOS 2.13.063F03

Source: [VID002 S3 VLB video card](https://github.com/ddanila/vintage-computer-inventory/blob/main/items/VID002-s3-vlb/README.md).
Owner-reported card markings: `FYI 94189886`, `FCCIXBGF9303`.
Card manufacturer and exact model remain unknown. The owner identifies the
EPROM as 27256; full manufacturer/speed markings were not supplied.

## Acquisition — 2026-11-17

Two T48 reads with `M27256@DIP28`, skipping electronic ID probing (`-x`),
match byte for byte. The preserved file is an unmodified 32,768-byte capture.
Header `55 AA 40` declares 32 KiB; the byte sum over that length is zero,
so the PC option-ROM checksum passes. No programming or emulator test was
performed. Original commands, reader hash and logs are under `evidence/`.

SHA-256: `8686bf841f5f6bd9b4ba88562d698c88b649d2cec52e3c0eb4207d91686afce1`

CRC32: `a43f1bce`

## Identification and comparison

The banner is `Phoenix S3 86C801/805 GENDAC Enhanced VGA BIOS. Version 2.13.063F03`.
Adjacent date strings at offset 0x184 are `09/16/93` and `06/07/94`; their
individual meanings have not been established. The image contains Phoenix
1987–1992 and S3 1992–1993 copyright messages.

This is distinct from [VID001's version 2.13.065](../phoenix-gendac-213065/).
No exact match or contiguous embedded copy was found in 1,113 local
[86Box ROM collection](https://github.com/86Box/roms) files sized 32–256 KiB,
at revision `52264223de5f3df1b51861481ee116eed47eca3e`. Limited searches by
version and CRC returned no results. This comparison does not prove uniqueness.
