# A fixed phase-47 preamble capture cannot select the receive readout

The [continuous preamble replay](RECEIVER-MASK04-PREAMBLE-SERIAL.md)
recovers data at 0° with the nominal row-pair readout and at 45° with
the diagonal row-pair/`3F8`-Y7 readout. Both rules also read the known
`11` reversal preamble correctly at 45°, so comparing preamble *dibits*
does not choose between them. A [first selector test](receiver_mask04_preamble_selector.py)
used bit 3 of an executed row-0 `3ED` Y byte at preamble symbol 16.
It chose correctly for fresh 0° and 45° data streams, but at 90° chose
the diagonal rule, leaving **15/16 data decisions unknown** although
the nominal rule gives 0/16 errors. Each case executed 576,047 real-PROM
microinstructions under the same fixed mask-`04` fixture.

A [four-value follow-up](receiver_mask04_preamble_class_lookup.py)
assigned the observed preamble row-0 bytes `FD` and `F2` to nominal,
and `F5` and `F3` to diagonal. It fit the 0°/45°/90°/135° development
angles. On 180°/225°/270°/315° holdout runs, it gave complete correct
decisions at three angles, but **180° yielded `F5` and 16/16 unknown**:
the nominal rule gives 0/16 errors there. The `F5` preamble byte thus
aliases 45° and 180° even though their data readouts differ.

The [direct alias replay](receiver_mask04_preamble_alias.py) runs a new
45°/180° pair with the same random data and checks *all 32* preamble
symbols. At ADC visit 47, every corresponding triple of executed bytes
(`3ED` row-0 Y, `3ED` row-3 Y, `3F8` Y) is identical between rotations.
The only triples are `(F5,00,5F)` and the final `(F5,F9,4F)`.

| Rotation | Nominal data readout | Diagonal data readout |
| ---: | ---: | ---: |
| 45° | 13/16 wrong | **0/16 wrong, full coverage** |
| 180° | **0/16 wrong, full coverage** | **16/16 unknown** |

No deterministic selector using only those phase-47 preamble triples can
choose the correct readout for both runs: it would receive identical
inputs and need different answers. This is a constraint on the proposed
*external* phase-class selector, not evidence that the DSC cannot track
carrier phase. Another ADC visit, full-rate samples, retained state, or
an executed phase-control path could distinguish the rotations. The
photo-compatible U12 row-0 latch alone at this visit does not solve C3.

The [first-selector report](results/receiver-mask04-preamble-selector.json),
[four-value report](results/receiver-mask04-preamble-class-lookup.json) and
[alias report](results/receiver-mask04-preamble-alias.json) retain trace,
ADC and capture hashes and all decisions. Reproduce from the microcode
directory with the three corresponding Python scripts. The input ADC
route, latch clocks, phase logic, serial timing and USART RxD path remain
labelled assumptions; C3 and G2 stay open.
