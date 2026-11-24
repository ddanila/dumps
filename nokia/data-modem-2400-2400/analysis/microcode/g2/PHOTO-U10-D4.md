# Corrected candidate U10 D4 → U5 Q3 route

The [DSC2847 front photograph](../../../photos/PXL_20261123_114926601.jpg)
shows a separate bright track between the vicinities of **U10 pin 14** and
**U5 pin 9**. The [PROM reader pin map](../../../microcode-810237c-810240c/README.md)
identifies U10 pin 14 as data bit 4. The
[TI SN74LS374 pinout](https://www.ti.com/lit/ds/symlink/sn74ls374.pdf)
identifies **U5 pin 9 as Q3, an output**. U5 pin 8, the corresponding D3
input, is the next pad to the right. U10 has 24 pins and U5 has 20, so the
same horizontal position has different pin numbers. The previous description
of this fragment as U10 D4 → U5 D3 was **incorrect**.

![Corrected U10 and U5 pad positions](results/photo-u10-d4-probe/corrected-pad.jpg)

If both endpoints are connected, a PROM data output and latch Q output may
share a net. That requires compatible output-enable timing. The photo
establishes neither that timing nor an onward route to Am2901 I1. This is
not a PROM-to-latch D-bit assignment. The earlier U10 D7/D6 → U5 D1/D2
candidates are separate.

[`photo_u10_d4_probe.py`](photo_u10_d4_probe.py) re-rectifies the original
front photo at 4000×2000 pixels, verifies its SHA-256 hash and flood-fills
that one bright component from `(1131,1400)`. At the recorded color threshold,
its bounds are `(1130,1341)–(1152,1662)`, spanning the two pad vicinities.
The [saved report](results/photo-u10-d4-probe.json) records the photo method,
pixel count and hashes. Dim pad gaps remain, so this is not measured
continuity.

As a bounded execution test, the probe substitutes the **counterfactual**
`I1 = 10.4` or `I1 = !10.4` into each of five
photo-constrained mappings. All ten 512-cycle real-PROM runs consume 39
controller-derived bits at the hypothetical D38E input. With direct polarity,
there are no ROM reads after an input group starts. With inverted polarity,
each complete group makes the same fixed three-address lookup. Neither case
changes its candidate ALU-Y output pattern across repetitions of a given bit,
or its output byte between 0 and 1. Inversion is a diagnostic alternative;
no inverter is traced on this candidate route. These substitutions do not
model simultaneous PROM/latch output drive or their enables.

The physical fragment suggests a possible shared output bus, while the tested
I1 destination remains speculative. It neither identifies the transmitter
nor closes off other U5 Q3 destinations, control modes, D-input routes or
clock phases.

The ROM-enable choice was another shared assumption in those ten runs. A
[follow-up sweep](photo_d4_gate_sweep.py) keeps the same direct/inverted I1
hypotheses in q1 and fitted-swapped, but tries all 137 previously fitted
diagnostic Am27S31 read gates. All **548** controller-fed runs complete with
38 full input groups. For direct `I1=10.4`, none of the gates gives more than
ten ROM reads. For inverted `I1=!10.4`, 69 gates per mapping do, but every
case still has one fixed ROM-address and candidate output pattern per repeated
bit value. The [saved gate report](results/photo-d4-gate-sweep.json) preserves
each gate and trace digest. These fitted gates are neither traced wiring nor
an exhaustive set of possible enable circuits; the result closes only this
counterfactual I1-source/gate neighborhood.
