# Unidentified board — Award VENUS-VIA BIOS, 1993-04-14

Owner described a 32-pin 27-series EPROM with an AWARD 486DX BIOS label.
Exact chip marking and source motherboard are unknown. Acquired 2026-11-22.

[128 KiB ROM](award-venus-via.bin) · [Analysis](evidence/analysis.json)

## Read verification

A read-only AT27C080 profile captured 1 MiB: eight identical 128 KiB blocks.
An independent AT27C010-profile read matches one block exactly. The first
64 KiB differs from the second, so 128 KiB is the smallest tested repeating
power-of-two image size. A 27C010-class device is inferred, not confirmed.
The 27C080 contact test flagged pin 30; the 27C010 contact test passed.
Pin 30 is unused on a 27C010. Electronic ID probing was skipped on both
reads; no programming was performed. Raw captures and logs are preserved.

## Contents and comparison

- Award Modular BIOS v4.20, ID `04/14/93-VENUS-VIA`.
- Cirrus CL-GD540X/542X VGA BIOS 1.00d, string `5422 08/07/92`.
- Whole-image and individual 64 KiB byte sums are zero modulo 256.
- No identical full image or 64 KiB half found among tracked dump files.
- No full-image or half-image match in the recorded 86Box ROM tree.
  The first 32 KiB exactly matches `video/cirruslogic/cl5422.rom` by Git
  blob hash; tree revision and comparison are in the evidence JSON.
- [The Retro Web FIC 486-VAL listing](https://theretroweb.com/motherboards/s/fic-486-val)
  has a related `04/24/93-VENUS-VIA` image with an S3 VGA BIOS. That differs
  in date and video hardware; the download returned HTTP 403, so no binary
  comparison was possible. This is not sufficient to identify our board as FIC.

No exact public match was established in these checks; this is not proof
that the image is absent from every archive. Retained as a candidate for
preservation. Motherboard operation has not been tested.
