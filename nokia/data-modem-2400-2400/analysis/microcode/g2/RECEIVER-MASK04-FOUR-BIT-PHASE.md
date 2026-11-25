# Four executed receive bits decode the grid, but not intermediate carrier phase

The [frozen readout](receiver_mask04_four_bit_phase.py) uses only four
executed byte bits at ADC visit 47 of each symbol: row-0 `3ED` Y bits 0,
1 and 3, plus transient `3F8` Y bit 7. It assigns a two-bit phase from
seven observed four-bit input codes, then differentially compares
successive phases to recover each dibit. The table was fitted to ten
earlier real-PROM traces at 0°, 45°, 90°, 135° and 180°, with
rotation-specific **development** label offsets; the offsets are not
inputs to the frozen decoder. The table was then tested on two new
random streams at every angle, each with a 32-symbol reversal preamble
followed continuously by 16 data symbols.

| Carrier rotations | Fresh traces | Preamble/data decisions | Errors | Unknown |
| --- | ---: | ---: | ---: | ---: |
| 0°, 45°, 90°, 135°, 180° | 10 | 470 | **0** | **0** |

The same four-bit table handles the nominal and diagonal phase classes
without selecting a separate lookup by carrier angle. The earlier nominal
rule still makes 13–15 data errors per fresh stream at 45°/135°, while the
earlier diagonal rule leaves 14–16 data decisions unknown at cardinal
angles. This is a stronger *conditional* readout of what the executed
`3F8` and `3ED` arithmetic retain. Each trace executes 576,047 real-PROM
microinstructions and verifies the candidate `3F8→3F9` capture edges.
The [machine report](results/receiver-mask04-four-bit-phase.json) includes
the frozen table, all symbol inputs, trace digests and decisions.

The [intermediate-angle challenge](receiver_mask04_four_bit_phase_between.py)
keeps the table unchanged on a third random stream at 15°, 30°, 60°, 75°,
105°, 120°, 150° and 165°. The independent reference receiver decodes
all eight waveforms, and each real-PROM loop completes. The four-bit rule
has **27 wrong and 152 unknown decisions of 376**; among 128 data dibits,
27 are wrong and 67 unknown. New input codes `0000` and `1000` explain
some unknowns, but not the wrong decisions. The
[collision audit](receiver_mask04_four_bit_collision_audit.py) integrates
the known reference dibits to relative phase labels: at 30°, 60°, 120°
and 150°, the *same* four-bit code occurs with two different required
phase states in a single trace. At every tested intermediate angle,
already-known codes disagree with the frozen table under every constant
phase offset. Filling two table entries cannot make this memoryless
four-bit phase decoder work across those angles. The
[angle report](results/receiver-mask04-four-bit-phase-between.json) and
[collision report](results/receiver-mask04-four-bit-collision-audit.json)
retain the failures and source hashes.

The photographed [U12 four-bit latch](../board/evidence/front-annotated.jpg)
could hold three row-0 bits, and U25's flip-flop capacity could hold the
transient `3F8` bit. Row-0 `3ED` occurs 13 microinstructions before
`3F8`, which in turn occurs 11 before row-3 `3ED`, so the ordering permits
such a **labelled** latch arrangement. No data pin, clock, gate or RxD
route has been traced to those packages. The phase table, phase register,
dibit mapping and bit serializer are external diagnostics, not executed
DSC instructions. C3 remains open; a useful next test should add a
second ADC visit or other executed state to resolve the intermediate-angle
collisions, then test the same controller handoff and photo-compatible
serial route. Missing continuity does not block that experiment.

Reproduce from the microcode directory with
`python3 g2/receiver_mask04_four_bit_phase.py`,
`python3 g2/receiver_mask04_four_bit_phase_between.py`, and
`python3 g2/receiver_mask04_four_bit_collision_audit.py`.
