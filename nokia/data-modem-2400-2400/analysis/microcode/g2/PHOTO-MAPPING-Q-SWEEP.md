# Initial-Q screen across the photo-compatible mappings

[The executable sweep](photo_mapping_q_sweep.py) runs all 256 initial Q bytes
for each of five Am2901 mappings, using the same photo-constrained E2-low,
E4-high fixture, real DSC 2847 PROMs and a controller-derived bit sequence
offered at the hypothetical D input at 38E. RAM starts at zero. Each reset
run is bounded at 512 microinstructions. The [saved report](results/photo-mapping-q-sweep.json)
contains all 1,280 outcomes, source hashes and 32 longer q2 ROM witnesses.
All runs complete cleanly.

| Mapping | Q seeds repeatedly visiting 38E | Q seeds with >10 selected ROM reads | Q seeds repeatedly visiting 392 or 396 |
| --- | --- | --- | --- |
| q1 photo-swapped | 32: Q≡5 mod 8 | None | 32: Q≡5 mod 8 |
| q2 photo-swapped | 32: Q≡5 mod 8 | 32: Q≡0 mod 8 | None |
| q3 photo-swapped | 32: Q≡5 mod 8 | None | 32: Q≡5 mod 8 |
| q4 photo-swapped | 32: Q≡5 mod 8 | Q=0 only | None |
| fitted-swapped | 32: Q≡5 mod 8 | None | 32: Q≡5 mod 8 |

The q2 ROM class looked promising in the aggregate, so every Q divisible by
8 was rerun with a full trace. Each executes 118 selected reads at word 129,
always at **one address per run**: `0x100 + Q + 1`. Its ALU Y at that word is
also one fixed byte per run. For example, Q=0 reads 101 and emits 253; Q=8
reads 109 and emits 236. These runs never visit the proposed controller input
at 38E. Thus this sustained q2 path reads a Q-selected constant; it does not
show a phase accumulator or symbol-dependent transmitter samples.

This screen reduces the chance that the earlier Q=5 choice alone hid the
desired behavior under these five mappings. It does not identify the board's
actual Q initialization or exclude another command entry, D source, ROM gate,
clock phase or output site. Those remain experiment variables rather than
goal blockers.
