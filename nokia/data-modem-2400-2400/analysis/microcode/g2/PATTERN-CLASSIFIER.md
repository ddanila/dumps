# Controller octet classifier at 1C07

The real 8031 ROM dispatch at `08E9` routes RAM34 states **83** and **A6**
through `0A38`, which calls `1C07` after two earlier routines. To isolate the
classifier, [pattern_classes.py](pattern_classes.py) executes `1C07` for every
RAM3A octet with RAM21.4 (the pending-octet flag) set. Other RAM, including
previous-octet RAM66 and counter RAM63, starts at zero. These are local
routine runs, not full received calls.

| State | RAM24 bits 3:2 = 00 | 01 | 10 | 11 |
| --- | ---: | ---: | ---: | ---: |
| 83 | 216 | 8 | 24 | 8 |
| A6 | 240 | 8 | 8 | 0 |

The eight `01`-class bytes in both states are `01 02 04 08 10 20 40 80`.
In A6, the eight `10`-class bytes are `03 06 0C 18 30 60 81 C0`.
State 83 additionally marks 16 other two-bit patterns as `10` and eight
three-bit patterns as `11`: `07 0E 1C 38 70 83 C1 E0`. All 256 runs return
without emulator errors and consume the pending-octet bit.

This identifies an actual state-dependent controller detector for received
octet patterns. It does **not** yet identify the V.26 ter rate-pattern
protocol: the selected sets have 40 and 16 bytes, not the plan's expected
34 legal octets, and the surrounding `0A38` calls and prior-octet history
may further qualify a match. The [full report](results/pattern-classes.json)
lists every byte in each class and records the ROM/source hashes.
