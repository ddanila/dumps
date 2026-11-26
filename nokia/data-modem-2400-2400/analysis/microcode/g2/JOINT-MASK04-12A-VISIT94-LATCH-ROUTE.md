# A paired-enable latch route can retain both receive captures

The [visit-94 gate holdout](JOINT-MASK04-12A-VISIT94-PHASE-GATE.md)
needs first `3F8` Y5–Y7 at visit `46`, second `3F8` Y7/Y4/Y6 at
visit `93`, row-0 Y0, and another `3F8` Y6 at visit `94`. Simply
clocking the same latch again at `94` would overwrite a needed earlier
bit. The photographed DSC 2847 inventory includes U14 `SN74LS75N`,
U12 `SN74LS175N` and U3 `74LS373 PC`. Their documented functions
provide a concrete **capacity and timing hypothesis**: U14 has two
independently enabled latch pairs [TI LS75](https://www.ti.com/lit/ds/symlink/sn74ls75.pdf),
U12 has four flip-flops on a common clock [TI LS175](https://www.ti.com/lit/ds/symlink/sn74ls175.pdf),
and U3 has eight latches on a common enable [TI LS373](https://www.ti.com/product/SN74LS373).

| Assumed stage | Captured value | Modeled cycle |
| --- | --- | ---: |
| U14 pair A | first Y5, Y7 at visit `46`; hold | 1,535 |
| U14 pair B | first Y6 at visit `46` | 1,535 |
| U12, two of four FFs | row-0 Y0 at visit `47` and copy of U14 pair-B first Y6 | 1,554 |
| U3, three of eight latches | second Y7, Y4, Y6 at visit `93`; hold | 3,039 |
| U14 pair B, reopened | later Y6 at visit `94`; first Y6 remains in U12 | 3,071 |

U12's candidate clock is 19 microcycles after the first Y capture.
The staged phase is ready 2,929 microcycles before the modeled first
RxC edge at cycle 6,000. U14's two enable pairs avoid disturbing
the first Y5/Y7 outputs when its Y6 latch is reused. U12's common
clock causes no conflict in this fixture: row-0 Y0 is identical at
visits `46` and `47` in every checked symbol.

The [staged replay](joint_mask04_12a_visit94_latch_route.py) applies
those events to ten saved real-PROM call/answer streams: the low-gain
development pair, both 1.15× and 1.25× control pairs, and the four
fresh-payload holdouts at carrier starts `133`/`135`. Across **650
symbols**, the staged seven-bit state and later Y6 match the earlier
capture rule exactly. All ten have zero modeled dibit errors and exact
line and executed controller bytes through the modeled 8251 handoff.
This checks storage capacity and timing under explicit inputs; the
decision holdouts remain the same four already reported, not ten new
holdouts.

A same-data control gives U14 one common enable at visit `94`, so Y5/Y7
are overwritten along with Y6. It makes **22–29 dibit errors per stream**
on the same ten captures. The paired-enable timing is therefore needed
for this staged route; package capacity alone would not preserve the
earlier state.

The data and enable nets, latch pulse widths, U12/U14/U3 electrical
timing, phase-bit gate package, RxD/RxC and SYNDET route remain
unidentified. The assumed U12 clock at visit `47` and two U14 enable
pulses must be constrained by the photographs or an independent
signal test. This route resolves a storage-capacity objection to the
later capture; it does not establish that Nokia wired these packages
this way or pass C3. The [machine report](results/joint-mask04-12a-visit94-latch-route.json)
contains every source trace hash and the staged-state/serial checks.
Reproduce from the microcode directory with
`python3 g2/joint_mask04_12a_visit94_latch_route.py`.

C3 and G2 remain open. Next challenge a distinct gain/carrier family
and seek a package-compatible realization of the full phase gate.
