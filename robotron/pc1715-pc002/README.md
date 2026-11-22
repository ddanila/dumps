# Robotron PC1715 PC002 ROMs

Owner-identified RF2 from socket **A25.3**, acquired 2026-11-22.
The owner describes a **white К573-series chip, not КС**. The complete chip
marking and physical ROM label have not been recorded.

[ROM](s502.a25.3) · [Manifest](manifest.json) · [Acquisition evidence](evidence/a25.3-20261122/)

## Identification and verification

Two independent 2,048-byte reads match exactly. The image is byte-identical
to [MB001 A25.3](../pc1715-mb001/s502.a25.3) and identifies as the known
**S502 boot ROM**, not a new variant. CRC32 `7b6302e1` and SHA-1
`e8f61763ff8841078a1939aa5e85a17f2af42163` match
[MAME's PC1715 reference](https://github.com/mamedev/mame/blob/master/src/mame/robotron/rt1715.cpp).
Identification is by contents, not a reported S502 label. No new execution
or retention test was performed during this acquisition.

## Acquisition

T48, explicit `t48-rf2` reader at MiniPro revision
`3e89e0fac87c9da21ab912cce2787aa3eaee8d07`, A9 rail-routing workaround,
requested VCC 5.18 V, read VPP routed to VCC. Both contact tests passed;
both reads reported pin-driver reset. Raw logs and session metadata are
preserved unchanged. No programming was performed; the session's programming
voltage setting is configuration metadata, not an applied programming pulse.

A25.1 and A25.2 have not yet been acquired in this collection.
