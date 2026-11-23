# Nokia external modem — another board, 2764 EPROM

Owner identifies this as a **2764 from another board of the same old Nokia
external modem** as the [810237C–810240C PROM set](../unknown-modem-810237c/).
The modem model, board identity, socket position and chip sticker remain unknown.
The photograph in the PROM set depicts that other board, not this EPROM's board.

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
8051-family code (reset LJMP 1EAAh). This is a preliminary architecture inference,
not a confirmed physical CPU identification. No clear product/version banner
was found among printable strings of at least eight characters. Firmware
function and operational validity have not been established by execution.

No contiguous match was found in 1,397 eligible 8–256 KiB files in the local
86Box ROM collection. Web searches for the CRC32 and SHA-256 found no relevant
public dump. This limited comparison does not establish uniqueness.

[Manifest](manifest.json) · [Acquisition evidence](evidence/)
