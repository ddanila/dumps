# A broader control-flow screen still leaves the candidate DAC words at zero

The [U10-bit table route](PHOTO-TABLE-PROMBIT-CONSUMER.md) carries real 8031
bytes through a sign table into internal instructions, but its first four
branch scenarios reach `392`/`39E` only with zero ALU output. The
[reproducible screen](photo_table_output_order_screen.py) keeps that same
q3, inverted-U10-bit-5, D349 and diagnostic AC=RST fixture, and tries all
**256 saved random branch seeds** for 2,500 microinstructions each.

| Reached-order condition | Seeds |
| --- | ---: |
| D349 writes R5 | 171 |
| A 3C5/3DA table call occurs | 106 |
| Candidate output word `392` or `39E` occurs | 134 |
| Candidate output occurs after a table call | 32 |
| D349 write → table call → candidate output, in that order | 8 |
| Such a chain with a nonzero internal `140`/`146` value before output | 4 |
| Nonzero ALU byte at `392`/`39E` after a table call | **0** |

Six of the eight full-order chains satisfy the strict 15-restart/stack/terminal
contract; the two other traces are included only for their reached event
order. For example, seed 184 reaches D349 at cycle 63, tables at 252/262,
consumer `140` at 271 with controller-dependent byte `E8` (selector `20`),
then `39E` at 687 and 859 with ALU byte `00`. Seeds 155 and 183 similarly
reach nonzero internal consumer bytes and later zero at `392`. This separates
two questions: the table result can be read, but these tested output words do
not carry it.

The [report](results/photo-table-output-order-screen.json) records every
full-order witness, its exact source, table and output cycles, and the
diagnostic strict-contract status. Random branch seeds and the AC override
are untraced; the U5 inversion/capture and D349 connection are hypotheses.
`392` and `39E` are candidate latch clocks rather than traced DAC08 clocks,
so their zero values do not rule out an output strobe elsewhere. The next
useful test is whether a photo-compatible latch clock can sample the varying
ALU bytes at `140`/`146` or whether another control path carries those bytes
to the output latch. Neither path yet supplies a sustained carrier.

## Diagnostic latch at the internal consumers

A [digital LS273 replay](photo_table_internal_latch.py) tests the first option
directly. It clocks the existing LS273 model at either `140` or `146`, with
Am2901 Y tentatively driving the latch D pins. Both clock choices capture
the same code sequence under the three strict branch seeds with nonzero
internal reads. Across four controller streams, each clock choice gives
**28 captures in 12 runs**, at most **three per run**. For selector `20`, the
per-run codes are:

| Branch seed | Candidate DAC input codes at `140` or `146` |
| ---: | --- |
| 155 | `00, 00, 7C` |
| 183 | `7C` |
| 184 | `00, E8, 00` |

These are controller-dependent under the candidate wiring. The only
photo-supported DAC data-bit relation, B5←LS273 Q4, can be computed from each
code, but the full Y-to-latch bit order and either clock route are untraced.
The sparse captures do not form the required sample-rate carrier. All 48
visits to `392`/`39E` in these 12 runs still have ALU Y=`00`.
The [latch report](results/photo-table-internal-latch.json) records every
capture, B5 candidate bit, and trace digest.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/photo_table_output_order_screen.py
```
