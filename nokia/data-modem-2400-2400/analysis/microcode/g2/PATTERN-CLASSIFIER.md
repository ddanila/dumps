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
octet patterns. The [full report](results/pattern-classes.json) lists every
byte in each class and records the ROM/source hashes. The 40/16 counts alone
do not identify the protocol; the standard comparison below tests their
rotation structure and repeated-octet behavior.

## Comparison with V.26 ter rate patterns

The 34 octets in [ITU-T V.26 ter §6.1.3](https://search.itu.int/history/HistoryDigitalCollectionDocLibrary/4.259.43.en.1036.pdf)
are **representatives of cyclic bit-rotation classes**, not a 34-byte
whitelist. Their rotations cover 254 nonconstant byte values. A
[reproducible comparison](rate_pattern_match.py) finds that the 40 bytes
marked in state 83 are **exactly** the rotations of the standard's first
five representatives, `01 03 05 07 09`: eight rotations per representative.
State A6 marks exactly the 16 rotations of `01 03`. Thus the earlier 40/16
versus 34 count was not a contradiction. These are selective subsets of the
standard's rate patterns; they are not the complete set of legal octets.

The same probe then preserves 8031 RAM across repeated calls to `1C07` and
one state step at `1000`. In state 83, three consecutive `03` octets leave
RAM63 at 3 and the state at 83; four leave RAM63 at 4 and advance the state
to 84. Four `06` octets (a rotation of `03`) and four `05` octets also advance
it. An interrupted `03 03 01 03` run ends with count 1 and remains at 83;
four unmarked `11` octets reset the count and remain at 83. This matches the
standard's requirement to detect at least **four consecutive error-free
rate-pattern octets**. In the ROM, `05A3` writes the descrambler result to
RAM3A, which `1C07` reads; the repeated-call experiment injects RAM3A at
that point and directs the PC between routines, so it does not establish a
continuous receive call or the physical input route.

The [saved comparison and chain traces](results/rate-pattern-match.json) retain
all 34 standard representatives, the exact set comparison, state/count
outcomes and source hashes. Reproduce with:

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/rate_pattern_match.py
```

Together, the rotation classes and four-octet transition strengthen the
V.26 ter controller-protocol identification. They do not yet identify the
DSC2847 signal-processing routines or satisfy G2's transmitter test.
