# Robotron PC1715 MB001 ROMs

Owner-identified RF2 from mainboard socket **A25.3**, acquired 2026-11-22.
The physical ROM label has not been recorded. Contents identify as the known
**S502 boot ROM**, not a newly discovered variant.

[ROM](s502.a25.3) · [Manifest](manifest.json) · [Acquisition evidence](evidence/a25.3-20261122/)

Two independent 2,048-byte reads match exactly. CRC32 `7b6302e1` and SHA-1
`e8f61763ff8841078a1939aa5e85a17f2af42163` match
[MAME's rt1715 S502 reference](https://github.com/mamedev/mame/blob/master/src/mame/robotron/rt1715.cpp).
SHA-256 also matches the reference used by our DAC PC1715 emulator checks.
This establishes reference-identical contents; no new execution or retention
qualification was performed during this acquisition.

Read using T48 and the explicit RF2 backend at revision
`3e89e0fac87c9da21ab912cce2787aa3eaee8d07`, with A9 rail routing and
requested VCC 5.18 V. Both contact preflights passed and both runs reported
pin-driver reset. Raw logs and session metadata are preserved unchanged.
No programming was performed. The session's programming-voltage setting is
configuration metadata; this was a read operation with read VPP routed to VCC.

A25.1 and A25.2 have not yet been acquired in this collection.
