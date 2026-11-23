# Nokia external modem — 810237C PROM set

The owner identifies the source as an old Nokia external modem, exact model
unknown. Four socketed PROMs are visible in the supplied
[board photo](photos/PXL_20261123_112138062.jpg). No inventory tag has been supplied.

| Board position | Sticker | Acquisition |
| --- | --- | --- |
| 10 | 810237C | Two matching 1,024-byte reads |
| 11 (owner; photo position number obscured) | 810238C (inferred association) | Two matching 1,024-byte reads |
| 17 | 810239C | Two matching 1,024-byte reads |
| 18 | 810240C | Pending |

The owner identifies chip 10 as **MMI 6381, 24-pin DIP**, with no further
readable suffix. Neighboring chips show partially exposed MMI 6381 markings;
their exact variants are not asserted from this photograph.

## Chip 10 acquisition — 2026-11-23

[Raw dump: chip10-810237c.bin](chip10-810237c.bin)

Two independent T48 reads using MiniPro's `82S181` custom read algorithm
produced identical, nonblank 1,024-byte images (146 distinct byte values).
Chip-ID probing was skipped. No programming was performed.

- SHA-256: `eae7ef704a0f6a1d262134826d364bd651a99351ebb395eaf19c78790b67e2bc`
- CRC32: `34da9bb6`
- Byte sum modulo 256: `0F`; no internal checksum scheme is established.

The initial invocation incorrectly included the display suffix `(custom)` in
the device name. It failed with “Device ... not found” before reading; its log
is retained. The successful CLI device name is `82S181`.

The [MMI 1981 databook](https://bitsavers.trailing-edge.com/components/mmi/_dataBooks/1981_MMI_Biploar_LSI_Databook_4ed.pdf),
printed pages 3-24–3-25 (PDF pages 37–38), documents the 6381 family as a 5 V,
1K × 8 bipolar PROM. Its pinout agrees with the local reader's type-8 mapping:
VCC 24, GND 12; A0–A9 on 8,7,6,5,4,3,2,1,23,22; D0–D7 on
9,10,11,13,14,15,16,17; enables 20/21 low and 18/19 high.

The repeat reads establish reproducibility, not modem operation. CPU/logic
architecture, PROM role and relationship among the four images are unconfirmed.
Searches for Nokia modem / 810237 and the CRC32 found no relevant public dump;
this limited search does not establish uniqueness.

[Manifest](manifest.json) · [Acquisition metadata and logs](evidence/chip10/)

## Chip 17 acquisition — 2026-11-23

[Raw dump: chip17-810239c.bin](chip17-810239c.bin)

Chip 17 was identified by the owner’s insertion report and the photo’s board
position and `810239C` sticker. The exposed marking identifies the MMI 6381
family; the exact suffix is not established. Two independent T48 reads using
the same `82S181` custom read algorithm, with ID probing skipped, produced
identical nonblank 1,024-byte images (69 distinct byte values). No programming
was performed. This image differs from chip 10.

- SHA-256: `52972d336004697ae3883784a477bbfa0bcccc5f003995d7288e0669ae7fa231`
- CRC32: `cf455d53`
- Byte sum modulo 256: `A0`; no internal checksum scheme is established.

Web searches for `810239C` / Nokia PROM and the CRC32 returned no results.
This does not establish uniqueness. PROM role, byte arrangement across chips
and modem operation remain unverified.

[Chip 17 acquisition metadata and logs](evidence/chip17/)

## Chip 11 acquisition — 2026-11-23

[Raw dump: chip11-810238c.bin](chip11-810238c.bin)

The owner inserted chip 11. Its association with sticker **810238C** is inferred
from the photo layout and acquisition sequence; the position number beside
810238C is obscured in the supplied crop. Read as the same MMI 6381 family;
exact chip markings were not independently reverified for this insertion.

Two independent read-only T48 captures with `82S181` and ID probing skipped
produced identical, nonblank 1,024-byte images (97 distinct byte values).
The image differs from both chip 10 and chip 17. No programming was performed.

- SHA-256: `260733c911c861d6ae19a28ce48717b1fe755e79636ab3da6f9b9b10e65a3939`
- CRC32: `659d0ae6`
- Byte sum modulo 256: `4C`; no internal checksum scheme is established.

Searches for `810238C` / Nokia PROM and the CRC32 returned no results; this
limited search does not establish uniqueness. Firmware role and arrangement
across the PROMs remain unverified.

[Chip 11 acquisition metadata and logs](evidence/chip11/)
