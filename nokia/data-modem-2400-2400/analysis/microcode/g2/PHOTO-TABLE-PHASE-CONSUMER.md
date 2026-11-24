# A candidate E2 phase lets the microprogram read a controller-fed table result

The previous [controller-byte run](PHOTO-TABLE-CONTROLLER-SOURCE.md) held the
photo-coupled E2/I0/A1 level low at every word. Under that fixture, the Am2901
source selector cannot read its B operand, and none of the table-written
R10–R13 values is consumed. Holding the level high everywhere permits B reads
but changes the 3C5/3DA arithmetic. The physical U5 latch clock is untraced,
so this experiment tests a **counterfactual phase schedule**: E2/I0/A1 low
during table words `3C5–3D4` and `3DA–3E9`, high at other words. E4/I7/A0
stays high. The [script](photo_table_phase_consumer.py) applies those coupled
levels to decoded real-PROM words; it does not claim that U5 actually follows
the microprogram address.

With actual 8031 USART-01 bytes offered at candidate D349, the q3 mapping
and four saved branch seeds give **16 clean diagnostic runs**, **132 table
calls**, and **144 reads of table-written registers outside the tables**.
Every call still follows the exact high-byte sign formula. The first
post-table consumers include `140`, `141`, `143` and `146`.

Seed 184 gives a concrete controller-to-table-to-consumer chain:

| Controller selector | First USART-01 byte at D349 | R5 | Table X output | ALU Y at `140` |
| --- | ---: | ---: | ---: | ---: |
| `00` | `06` | `07` | `0707` | `07` |
| `20` | `E7` | `E8` | `E8E8` | `E8` |
| `40` | `F9` | `FA` | `FAFA` | `FA` |
| `60` | `F8` | `F9` | `F9F9` | `F9` |

This is the first tested route here in which a real controller byte affects
a sign-table operand **and** a later instruction reads the resulting value.
It identifies E2 timing as a useful discriminating hypothesis. It does not
establish the physical latch phase, a continuous sample loop, or a line
signal: each run consumes only one to three controller bytes, the AC=RST
continuation at `084` is hypothetical, upstream branches are scenario-driven,
and all **20 visits to output candidate `39E`** still have ALU Y=`00`.
`140` is an internal consumer, not a traced DAC08 latch clock.

The [report](results/photo-table-phase-consumer.json) contains the per-call
source/output pairs, downstream register reads, output-candidate values,
trace digests and source hashes. A next candidate should replace the PC-based
E2 schedule with a plausible U5 clock/hold rule and test whether the consumed
value can reach a changing DAC-bound code.
A [U10-data-bit candidate](PHOTO-TABLE-PROMBIT-CONSUMER.md) replaces the
address-assigned level with inverted real PROM bit 5 while holding U10 E2
low. It reproduces the table/consumer chain and admits all four table
entries under controller dibits, but its inverter and capture clock are
untraced.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/photo_table_phase_consumer.py
```
