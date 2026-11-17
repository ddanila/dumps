# VID004 — ASUS GMIO-470 VGA BIOS v1.1

Source: [VID004 ASUS VLB card](https://github.com/ddanila/vintage-computer-inventory/blob/main/items/VID004-asus-gmio470/README.md),
serial `37301764`, FCC ID `JL7ASUSGMIO470`, per owner.

## Acquisition — 2026-11-17

28-pin 27-series EPROM, exact type unknown. Two T48 reads using
`M27256@DIP28` with electronic ID probing skipped (`-x`) match exactly.
The preserved canonical file is the unmodified 32,768-byte read, starting
`55 AA 40`. It declares 32 KiB and has a zero byte sum over that length,
so its VGA option-ROM checksum passes. No smaller 2/4/8/16 KiB image repeats
across the capture. No programming or emulator test was performed.

SHA-256: `5b746085f53b0f97a291f87cbae4bf402b8651794693da874c56681d3033f1f4`

CRC32: `3df1a89c`

### Capacity remains unresolved

Two further `M27C512@DIP28` reads match each other. Each returns 64 KiB with
an all-FF lower 32 KiB and an upper 32 KiB exactly matching the canonical BIOS.
The full unmodified probe is preserved as `evidence/27c512-profile-64k.bin`.
This does not conclusively distinguish 27256-family profile-dependent read
behavior from a 27C512 storing the BIOS in its upper half. Do not infer the
physical capacity solely from this result. Full chip markings would help.

## Embedded identification

- `GMIO-470 VGA BIOS Version 1.1`
- `ASUSTeK Computer Incorporation, 1993`
- `Cirrus Logic GD-54xx VGA`
- Cirrus Logic copyright 1992; Quadtel copyright 1987–1990.

The model and graphics-chip family are identified from firmware. Physical
chip markings, board revision and installed video-memory size are not recorded.

## Public comparison

No exact match or contiguous copy found among 1,113 local
[86Box ROM collection](https://github.com/86Box/roms) files of 32–256 KiB,
revision `52264223de5f3df1b51861481ee116eed47eca3e`. Limited searches by CRC
and model did not identify an exact matching binary. This is not proof of
uniqueness. Commands, hashes, logs and comparison metadata are in `evidence/`.
