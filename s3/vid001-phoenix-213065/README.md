# VID001 — Phoenix S3 86C801/805 GENDAC BIOS 2.13.065

Source: [VID001 S3 805 VLB video card](https://github.com/ddanila/vintage-computer-inventory/blob/main/items/VID001-s3-805-vlb/README.md).
The owner identifies the EPROM as 27C256; full manufacturer and speed markings
were not supplied. Card manufacturer and exact model remain unknown.

## Acquisition — 2026-11-17

Two independent T48 reads using `M27C256B@DIP28` with ID probing skipped
(`-x`) match exactly. The unmodified 32,768-byte image starts `55 AA 40`,
declares 32 KiB, and has byte sum zero modulo 256 over that entire length:
the PC option-ROM checksum passes. No programming or emulator test was performed.
Commands, reader hash, logs, strings and comparison notes are in `evidence/`.

SHA-256: `075cdf3920e5d9dd6a599f6bb1e4fe121553802e781670931cdaf12a2e8ebd1a`

CRC32: `bf83524f`

## Embedded identification

- `Phoenix S3 86C801/805 GENDAC Enhanced VGA BIOS. Version 2.13.065`
- Phoenix Technologies copyright 1987–1992; S3 Incorporated copyright 1992–1993.
- Adjacent date strings at offset 0x184: `08/12/94` and `10/20/94`.
  Their individual meanings have not been established.
- `S3 Incorporated. 86C801/805`.

## Public comparison

No exact match or contiguous embedded copy was found among local
[86Box ROM collection](https://github.com/86Box/roms) files from 32 to 256 KiB,
at revision `52264223de5f3df1b51861481ee116eed47eca3e`. The related S3 candidate
list is retained in `evidence/public-comparison.json`. Limited searches by
version and CRC did not locate an exact matching binary. This does not establish
uniqueness; the version string alone is insufficient to identify an exact image.
