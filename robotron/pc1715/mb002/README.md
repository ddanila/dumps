# Robotron PC1715 MB002 — A25.3 originally from MB001

Owner-identified **U2716C35**, socket **A25.3**, acquired 2026-11-22.
The owner reports that this chip originally came from **MB001** and was
swapped to **MB002**. MB001 began booting after the ROM swap. The chip's
physical ROM label was not recorded; its working condition was uncertain.
These board IDs describe acquisition and owner-reported history, not factory provenance.

[ROM](s502.a25.3) · [Manifest](manifest.json) · [Evidence](evidence/a25.3-original-mb001-20261122/)

## Result

Two independent 2,048-byte reads match exactly. Contents are **S502**,
byte-identical to the boot ROMs acquired from [MB001](../mb001/)
and [PC002](../pc002/). CRC32 `7b6302e1` and SHA-1
`e8f61763ff8841078a1939aa5e85a17f2af42163` match
[MAME's known S502 reference](https://github.com/mamedev/mame/blob/master/src/mame/robotron/rt1715.cpp).

No content corruption is visible in these reads. This does not establish that
the chip works reliably on the motherboard or explain why swapping ROMs fixed
MB001's boot. Access timing, socket contacts, electrical margins and retention
were not tested. No new emulator execution or hardware boot was performed.

## Acquisition

T48 explicit `t48-2716-read` profile (`read2716`), nominal 5 V VCC/read VPP,
ordinary digital A9 addressing, MiniPro revision
`3e89e0fac87c9da21ab912cce2787aa3eaee8d07`. Both contact preflights passed;
both reads reported pin-driver reset. Raw logs and session metadata are
preserved unchanged. No programming was performed.
