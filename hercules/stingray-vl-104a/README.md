# VID003 — Hercules Stingray VL BIOS 1.04.A

Source: [VID003 Hercules VLB video card](https://github.com/ddanila/vintage-computer-inventory/blob/main/items/VID003-hercules-stingray-vl/README.md),
serial `297754`, FCC ID `JQDA2228AV9401` (owner-supplied markings).

## Acquisition — 2026-11-17

28-pin 27-series EPROM, exact manufacturer/type markings unknown. Two T48 reads
using `M27256@DIP28` with electronic ID probing skipped (`-x`) match exactly.
The preserved image is an unmodified 32,768-byte read. Header `55 AA 40`
declares 32 KiB and the byte sum over that length is zero: VGA option-ROM
checksum passes. No smaller 2/4/8/16 KiB image repeats across the capture.

A further `M27C512@DIP28` read yields two identical copies of the 32 KiB image,
consistent with a 27256-class chip. This does not distinguish address mirroring
from a larger chip deliberately containing duplicate halves; type remains
provisional. The full probe is retained in the local session named in the
manifest. No programming or emulator test was performed.

SHA-256: `68f5ec7f29018e3c31085f7ba3a5c4e9789144b566887dcc1eb14d9605725370`

CRC32: `ee0347f6`

## Embedded identification

- `Stingray VL        g1ALG-2228 V.1.04.A`
- `Hercules Computer Technology, Inc.`
- `Copyright(c) 91-93, ALI & Quadtel Corp.`
- `VESA for AVANCE LOGIC, INC.`
- Adjacent date strings at offset 0xDD: `10/13/90` and `05/04/94`.
  Their individual meanings have not been established.

The model and chipset-family identification comes from the BIOS; full physical
chip markings and board revision have not yet been recorded.

## Public comparison

No exact match or contiguous copy found among 1,113 local
[86Box ROM collection](https://github.com/86Box/roms) files of 32–256 KiB,
revision `52264223de5f3df1b51861481ee116eed47eca3e`. Limited web searches by
CRC and model/version did not identify a matching binary. This is not proof
of uniqueness. Commands, hashes, logs and comparison metadata are in `evidence/`.
