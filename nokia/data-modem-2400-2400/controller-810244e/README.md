# Nokia Data Modem 2400/2400: controller EPROM 810244E

The 2764 EPROM holding the 8031 controller program. It comes from board
**DSU 3556 / 1177954** of the [Nokia Data Modem 2400/2400](../), which carries
an Intel P8031 and two 8251A USARTs. The owner confirmed the sticker
**810244E**; the socket position is unrecorded.
[Board photo](../photos/PXL_20261123_114723348.jpg).

## Acquisition — 2026-11-23

Two independent read-only T48 captures using `M2764A@DIP28`, with chip-ID
probing skipped, yielded identical nonblank 8,192-byte images. No programming
or byte repairs were performed.

[Raw dump](nokia-modem-other-board-2764.bin)

- SHA-256: `daf854c513cd427664bb345f511afc2d38441e5002e4a85389d289aedbfc0038`
- CRC32: `e0338911`
- Byte sum modulo 256: `70`; no internal checksum scheme is established.
- Distinct byte values: 249.

The opening bytes `02 1E AA` and vector-area patterns are consistent with
8051-family code (reset LJMP 1EAAh). The later photo confirms an Intel P8031 on the source board. No clear product/version banner
was found among printable strings of at least eight characters. The later investigation executes this ROM with synthetic hardware; see below.

No contiguous match was found in 1,397 eligible 8–256 KiB files in the local
86Box ROM collection. Web searches for the CRC32 and SHA-256 found no relevant
public dump. This limited comparison does not establish uniqueness.

[Manifest](manifest.json) · [Acquisition evidence](evidence/)

The same modem also supplied an [Am27S31DC PROM from its last board](../am27s31dc-prom/), preserved as a separate 512-byte image.

[Hardware identification, controller execution harness and results](../) document the subsequent investigation and its limitations.
