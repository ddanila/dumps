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

## A25.2 character ROM

Owner-identified **U2716C35**, acquired from MB001 socket A25.2 on
2026-11-22. Two independent 2,048-byte reads match exactly and identify as
**S643**, the character ROM listed for MAME's Latin/Cyrillic `rt1715lc` set.
This is a known image, not a newly discovered variant. Its physical ROM label
has not been recorded; S643 is identification by contents.

[ROM](s643.a25.2) · [Acquisition evidence](evidence/a25.2-20261122/)

CRC32: `ea37f0e6`; SHA-1: `357760974d944b9782734504b9820771e7e37645`.
Both match the [MAME reference](https://github.com/mamedev/mame/blob/master/src/mame/robotron/rt1715.cpp).
Used the explicit `t48-2716-read` profile (`read2716`), with nominal 5 V
VCC/read VPP and ordinary digital A9 addressing. Both contact tests passed;
both reads reported pin-driver reset. No programming or new execution test
was performed. Raw logs and session metadata are retained unchanged.

## A25.1 character ROM

Owner-identified **U2716C35**, acquired from MB001 socket A25.1 on
2026-11-22. Two independent 2,048-byte reads match exactly and identify as
**S605**, the other character ROM listed for MAME's Latin/Cyrillic `rt1715lc` set.
The physical ROM label has not been recorded; S605 is identification by contents.

[ROM](s605.a25.1) · [Acquisition evidence](evidence/a25.1-20261122/)

CRC32: `38062024`; SHA-1: `798f62d4adeb7098b7dcbfe6caf28302853ee97d`.
Both match the [MAME reference](https://github.com/mamedev/mame/blob/master/src/mame/robotron/rt1715.cpp).
Used the explicit `t48-2716-read` profile (`read2716`), with nominal 5 V
VCC/read VPP and ordinary digital A9 addressing. Both contact tests passed;
both reads reported pin-driver reset. No programming or new execution test
was performed. Raw logs and session metadata are retained unchanged.

All three mainboard ROMs are now acquired: A25.3 S502, A25.2 S643 and
A25.1 S605. Their hashes match the known Latin/Cyrillic PC1715 reference set;
none of these acquisitions is an unknown variant.


## Board-swap provenance clarification

The owner subsequently reported a ROM swap between MB001 and MB002, after
which MB001 began booting. The U2716C35 A25.3 originally from MB001 is now
recorded under [MB002](../pc1715-mb002/); its contents match this collection's
RF2 S502 exactly. This collection records the chips associated with MB001 at
acquisition, not necessarily its original factory-installed ROMs.
