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

## Pin-function audit of the visible tracks

A closer look at the original-size front image places the eight ordered
tracks against the eight signal pads on the facing banks: 74LS273 right
pins 19–12 and 74LS373 left pins 2–9. The chips' notches are at the top.
The [TI 74LS273 pinout](https://www.ti.com/lit/ds/symlink/sn74ls273.pdf)
and [TI 74LS373 pinout](https://www.ti.com/lit/ds/symlink/sn74ls373.pdf)
give this candidate pairing:

| 74LS273 pin/function | 74LS373 pin/function | Type |
| --- | --- | --- |
| 19 / 8Q | 2 / 1Q | Q–Q |
| 18 / 8D | 3 / 1D | D–D |
| 17 / 7D | 4 / 2D | D–D |
| 16 / 7Q | 5 / 2Q | Q–Q |
| 15 / 6Q | 6 / 3Q | Q–Q |
| 14 / 6D | 7 / 3D | D–D |
| 13 / 5D | 8 / 4D | D–D |
| 12 / 5Q | 9 / 4Q | Q–Q |

The [pin-pairing audit](results/photo-ded-latch-pin-pairing.json) checks the
threshold-stable track order and records the source photos and pinouts. If
those tracks contact the adjacent pads, they are four output-to-output and
four data-to-data links; **none is a 74LS373 Q→74LS273 D link**. That
disfavors the simple serial 74LS373-hold→74LS273-copy explanation for these
front-side tracks, even though that model gives the best conditional line
scores. It does not rule out hidden/back-side Q→D connections or another
way for the 74LS273 to capture settled `12A` Y. The [reverse-side photo](../../../photos/PXL_20261123_114901193.jpg)
has dense tracks and was not registered pad by pad. The direct 74LS273
clock-before-new-`127`-Y hypothesis remains runnable and should be tested
against the gate/Y delay ordering before assigning the physical route.

The [two-stage `12A` replay](JOINT-MASK04-TX-12A-TWO-STAGE-LATCH.md)
demonstrates what one such assumed circuit would output, **not** that these
eight traces carry its 74LS373 Q→74LS273 D links. The
[B5 topology comparison](JOINT-MASK04-TX-LATCH-B5-DISCRIMINATOR.md) now
runs that hold against a shared-Y late-clock route on the same real-PROM
stream. They predict 698/832 call and 696/832 answer differences at the
photo-suggested DAC08 B5 input, conditional on an untraced Y4→74LS273 D4
wire. A pin observation or another photo-compatible route can narrow them;
missing continuity does not block C2 work or pass C2.

Reproduce from the microcode directory with:

```sh
python3 g2/photo_ded_latch_bus.py
```
