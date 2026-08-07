# Unidentified K573RF5 set 41-44

Four Soviet `К573РФ5` (`K573RF5`, 2716-compatible) 2 KiB EPROMs were removed
from an unidentified PCB. The owner reports that the board is not from a Juku
computer and that the four devices were connected in parallel. No system or
board identity is currently claimed.

## Physical mapping

| PCB position | Chip label | Dump |
|---:|---:|---|
| 1 | 44 | [`pcb1-label44.bin`](pcb1-label44.bin) |
| 2 | 43 | [`pcb2-label43.bin`](pcb2-label43.bin) |
| 3 | 42 | [`pcb3-label42.bin`](pcb3-label42.bin) |
| 4 | 41 | [`pcb4-label41.bin`](pcb4-label41.bin) |

## Acquisition

- Date: 2026-08-07
- Programmer: Willem PCB5.0E, dedicated read-only 2716 routing
- Reader: [`ddanila/willem-v30`](https://github.com/ddanila/willem-v30)
- Transport: [`ddanila/dosravi`](https://github.com/ddanila/dosravi)
- Read conditions: 5 V VCC, software VPP disabled
- Size: exactly 2,048 bytes per chip
- Repeatability: label 44 matched across ten reads; labels 43, 42, and 41
  matched across two reads each

Every read completed with safe VCC/VPP shutdown. The images are non-uniform
and all four are distinct. A scan of the individual, concatenated, and
byte-interleaved images found no meaningful strings in ASCII, high-bit ASCII,
CP866, KOI8-R, ISO-8859-5, or Windows-1251. The data appears predominantly to
be executable code and lookup tables, but that does not identify the system.

## Checksums

| Dump | CRC16-CCITT | CRC32 | SHA-256 |
|---|---:|---:|---|
| `pcb1-label44.bin` | `AFD3` | `633D0952` | `f15117b3914b8df9779ea8fe608e012bb462d0ee68e9cf3c5772e2b96bfe8c3e` |
| `pcb2-label43.bin` | `784A` | `B02C841B` | `70b32dcd2e60c757495933d1e12f4e3a780c68888a50b24cd92ebd5d2d859b47` |
| `pcb3-label42.bin` | `708D` | `0B92EAEC` | `4015ef546151d9fc396cb0ff2ae0dc51e0284d0258e9ddae97adf84bfe386607` |
| `pcb4-label41.bin` | `8B8C` | `51798125` | `95111798e9e19b0c54ee015d0dda6f86832e6645af6fe6b5ab2eda9d6dcbc60a` |

`SHA256SUMS` is provided for direct verification. `manifest.json` contains the
same mapping in machine-readable form.
