# Eight visible tracks join the DED 3558 latch pad regions

The [DED 3558 front photo](../../../photos/PXL_20261123_114854803.jpg)
places a 74LS273 beside a 74LS373 near the DAC08HP. The
[pixel audit](photo_ded_latch_bus.py) isolates the gap between the
74LS273's right pad bank and the 74LS373's left pad bank at original-photo
rectangle `(1642,3230)–(1895,3511)`. Two slightly different cyan-track
thresholds each find **eight** separate components crossing the gap; their
endpoint y coordinates agree within two pixels. The
[report](results/photo-ded-latch-bus.json) records all eight paths, the
photo SHA-256 and both thresholds.

This is stronger evidence for a visible **bus bundle** than mere chip
proximity, but it does not identify a serial latch chain. The analyzed
rectangle ends before the component pads; copper hidden beneath packages,
back-side traces and vias are not resolved. Neither signal direction nor
individual D/Q pin continuity follows from eight matching tracks. The
[TI 74LS373 datasheet](https://www.ti.com/lit/ds/symlink/sn74ls373.pdf)
says its outputs follow D while enable is high and can be tri-stated with
output control; the [TI 74LS273 datasheet](https://www.ti.com/lit/ds/symlink/sn74ls273.pdf)
describes an edge-triggered register. Thus a shared or switched bus and a
two-stage hold remain different, photo-compatible hypotheses.

The [two-stage `12A` replay](JOINT-MASK04-TX-12A-TWO-STAGE-LATCH.md)
demonstrates what one such assumed circuit would output, **not** that these
eight traces carry its 74LS373 Q→74LS273 D links. Next compare a shared
Y-input/tri-state-output hypothesis with the hold-stage timing on the same
real-PROM stream, and identify a pin or output observation that separates
them. Missing continuity does not block that experiment or pass C2.

Reproduce from the microcode directory with:

```sh
python3 g2/photo_ded_latch_bus.py
```
