# A candidate input updates the sign-table source high byte

The earlier [restart run](PHOTO-TABLE-RESTART.md) found fixed source pairs for
two saved branch scenarios. A broader **diagnostic** screen finds other saved
scenarios that visit instruction `349`, write source register R5, and later
call the 3C5/3DA sign tables. This tests a specific route for changing the
table operand; it does not establish that the board connects this input to
`349` or restarts the sequencer at `084`.

The [reproducible run](photo_table_source_update.py) holds the same photo-pin
levels, predecessor-Y table dispatch, and first-15-arrivals AC=RST override.
It sets external D only at `349` and leaves other D reads at zero. Four saved
random branch seeds (22, 116, 184, 245), two photo-compatible mappings
(q1/q3), and seven D bytes give **56 clean runs and 462 reached table calls**.
Every call matches the [exact sign formula](PHOTO-TABLE-EXACT.md).

| Mapping | D at 349 | R5 write at 349 | Later source X high byte |
| --- | ---: | ---: | ---: |
| q1 | any tested byte | `01` | `01`, independent of D |
| q3 | `00`, `01`, `55`, `80`, `FE` | `01`, `02`, `56`, `81`, `FF` respectively | same as R5 |
| q3 | `FF` | no R5 write at 349 | `00` in these fixtures |

The q3 relationship holds for all four seeds. For example, seed 116 calls the
tables with source high bytes `(00,FF)` before the update and `(56,FF)` after
`D349=55`. Its output follows the chosen sign entry with replicated `5656`
as the X magnitude. In q1, the same D changes neither R5 nor the table
source. `D=FF` inhibits the q3 write at `349`; it must not be reported as an
`FF→00` update.

This is a conditional **D349 → R5 → sign-table output** chain. The external
D source, photo mapping, upstream branch conditions and sequencer restart
remain hypotheses. There is no demonstrated stream of advancing source bytes,
phase accumulation, Am27S31 read at this site, or DAC08 output strobe. The
next useful experiment is to test candidate ROM, ADC and controller routes
that can change D at `349` over time and to look for a reached output latch.
No new photo or continuity measurement is required to run those candidates.

The [report](results/photo-table-source-update.json) records each input byte,
R5 write, call source/output, restart count, trace digest and source hashes.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/photo_table_source_update.py
```
