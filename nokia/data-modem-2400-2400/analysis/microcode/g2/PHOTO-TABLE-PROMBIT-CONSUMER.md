# A real U10 bit reproduces the table/consumer phase pattern

The earlier [address-assigned phase](PHOTO-TABLE-PHASE-CONSUMER.md) was only a
diagnostic schedule. U10's real PROM dump offers a more concrete **candidate
data source**: inverted U10 data bit 5 is low at all **32 words** of the two
3C5/3DA sign tables and high at the reached consumer words `140`, `141`,
`143` and `146`. It differs from the prior address schedule at 235 of 1,024
microaddresses, so this is not simply the same PC rule restated.

The [byte-only execution](photo_table_prombit_consumer.py) assumes an
untraced inverted U10-D5→U5-D0 route, U5 Q0→Am2901 I0/A1, and a capture
at each decoded microaddress. U10 E2 stays low, so its PROM data is valid
under the modeled read condition. E4/I7/A0 stays high. With actual 8031
USART-01 bytes offered at candidate D349, 16 q3 runs make **132 table
calls** and **144 later reads of table-written registers** outside the
tables. All table calls follow the high-byte sign formula. All 16 trace
digests differ from the address-assigned phase experiment while preserving
this data path.

The [combined byte/dibit execution](photo_table_prombit_symbols.py) also
offers successive LSB-first dibits from those real USART-01 bytes at candidate
table predecessor inputs `3C1` and `3D6`, in the baseline call order. It
selects **all four table entries** across 132 reached calls; every output
matches the exact sign formula, and 144 table-output reads occur downstream.
Seed 184 gives a compact witness:

| Controller selector | First byte at D349 | Dibit-selected table entry at call 262 | Table X output | ALU Y at `140` |
| --- | ---: | ---: | ---: | ---: |
| `00` | `06` | 1 | `0707` | `07` |
| `20` | `E7` | 1 | `E8E8` | `E8` |
| `40` | `F9` | 2 | `0506` | `05` |
| `60` | `F8` | 2 | `0607` | `06` |

This demonstrates a **conditional controller byte + dibit → table result →
internal consumer** chain using real PROMs and controller output. Its
electrical status is still a hypothesis: neither the inverter and U5 data
route nor the per-word capture clock is traced. Supplying the same controller
stream as full bytes at D349 and scheduled dibits at table predecessors is
also an untraced fan-out/timing assumption. The branch bus, upstream
conditions and diagnostic AC=RST continuation remain assumed.

The work does **not** establish a transmitter. Each run consumes only one to
three bytes at D349, and all **20 reached visits to output candidate `39E`**
still have ALU Y=`00`. No DAC08 latch strobe or sustained waveform is
identified. The next test should constrain the U5 source and clock against
the photos and real PROM enables, then seek a continuing path from the
table consumer to a changing DAC-bound code.
A [256-seed control-flow screen](PHOTO-TABLE-OUTPUT-ORDER.md) finds eight
diagnostic paths that reach D349, a table, then `392`/`39E`; four have a
nonzero internal `140`/`146` byte, but every later candidate output byte is
zero. This narrows the output-clock question without proving either candidate
word is the physical latch strobe.
A [full U10 data-bit/polarity screen](PHOTO-U10-Q0-SOURCE-SCREEN.md) confirms
that inverted bit 5 is the only one of 16 tested source choices that preserves
every sign-table formula and a nonzero downstream consumer in four diagnostic
branch fixtures. The inversion and U5 wiring remain untraced.

The [byte-only report](results/photo-table-prombit-consumer.json) and
[combined report](results/photo-table-prombit-symbols.json) record calls,
consumer reads, candidate output values, trace digests and source hashes.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/photo_table_prombit_consumer.py
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/photo_table_prombit_symbols.py
```
