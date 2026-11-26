# Changed-phase four-row capture and row-clock qualification

The [phase-112 run](joint_mask04_12a_all_row_phase112.py) extends the earlier
[four-row capture](JOINT-MASK04-12A-ALL-ROW-LATCH.md) to two different fresh
payloads and R1 carrier offset 112. It uses the frozen 22-state phase gates
and the same labelled q3/mask-04 DAC, analog and ADC scenario. For each mode,
it regenerates the controller-fed transmitter and executes the complete
real-PROM receiver, recording all four `3ED` Y rows at visits 46, 47, 93 and
94 in every symbol. The transmitter, line PCM, ADC and receiver trace hashes
match the earlier phase-112 captures; row-0 and row-3 bytes match them too.

| Assumed U12 latch source at visit 46 | Call `40` errors / 64 | Answer `60` errors / 64 |
| --- | ---: | ---: |
| Row 0, selected by a modulo-four qualifier | **0** | **0** |
| Row 1 | 21 | 18 |
| Row 2 | 21 | 18 |
| Row 3, final value after an unqualified every-row clock | 19 | 15 |

Rows 1 and 2 are zero at every checked visit in both executions. If a raw
`3ED` clock reaches U12 on all four rows, row 3 is the final stored value;
under this readout it fails. The candidate U24 low-bit counter must instead
qualify row 0, equivalent to pre-increment `00` in the earlier counter-phase
screen. This changed carrier phase confirms that the required logical row
selection is not peculiar to the offset-88 training fixture. It does not
show that U24 drives U12, identify a gate path, or prove that the board uses
this seven-bit phase consumer. The first dibit and serial handoff remain the
explicit assumptions of the [photo-latch replay](JOINT-MASK04-12A-ROW0-PHOTO-LATCHES.md).

The [machine report](results/joint-mask04-12a-all-row-phase112.json) saves
520 five-value snapshots, all wrong-decision indices, hashes and assumptions.
Reproduce from the microcode directory with:

```sh
python3 g2/joint_mask04_12a_all_row_phase112.py
```

C3 remains open and G2 active. Next test a photo-compatible raw-PROM decode
and U24/U12 gate timing around `3ED→3EA` against the row-0-only requirement;
keep the untraced nets as assumptions rather than waiting for continuity.
