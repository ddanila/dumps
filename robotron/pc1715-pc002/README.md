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

## A25.2 character ROM

Owner-identified **2716**, acquired from PC002 socket A25.2 on 2026-11-22.
The complete chip marking and physical ROM label have not been recorded.
Two independent 2,048-byte reads match exactly and identify as **S619**,
listed for MAME's standard `rt1715` set. This differs from MB001's S643
A25.2 image, but is a known reference image rather than an unknown variant.

[ROM](s619.a25.2) · [Acquisition evidence](evidence/a25.2-20261122/)

CRC32: `98647763`; SHA-1: `93fba51ed26392ec3eff1037886576fa12443fe5`.
Both match the [MAME reference](https://github.com/mamedev/mame/blob/master/src/mame/robotron/rt1715.cpp).
Used the explicit `t48-2716-read` profile (`read2716`), with nominal 5 V
VCC/read VPP and ordinary digital A9 addressing. Both contact tests passed;
both reads reported pin-driver reset. No programming or new execution test
was performed. Raw logs and session metadata are retained unchanged.

A25.1 has not yet been acquired in this collection.
