# Independent Am2901 slice instruction fields reopen ROM operand use

The [two possible tracks between U2 and U8](PHOTO-SLICE-LINK.md) challenge
the shared nine-bit instruction used by the existing mappings. The emulator
now accepts a separately decoded, provenance-labelled `i_high` field for U8,
while the scenario can still impose candidate U8 I4←U2 I1 and U8 I6←U2 I2
links. This allows the two slices to read different control-PROM bundles
without pretending that their full wiring is known. ROM D-use accounting
counts either slice selecting D.

The [screen](independent_slice_fields.py) keeps the existing q3 register,
branch, input and clock hypotheses. It compares four instruction layouts:

| Layout | Lower U2 instruction | Upper U8 instruction |
| --- | --- | --- |
| Shared control | Existing q3 field | Same field, with two crosslinks |
| Upper pair only | Existing q3 field | U10→U17 and U11→U18 source-lane substitution |
| Separated pairs | U17→U10 and U18→U11 substitution | Upper-pair substitution above |
| Separated, reversed upper | Same lower field | Upper-pair data-bit indices reversed |

The lane ownership and bit orders are **hypotheses** suggested by the PROM
and latch placement, not traced U29/U30-to-U8 or U5/U6-to-U2 connections.
Every layout ran all 256 startup Q bytes for 512 real-PROM cycles; the screen
then ran Q=0, Q=5 and the seed with most selected ROM reads for 1,580 cycles.
At Q=5 it supplied 128 unchanged 8031 scrambler bits and two controls of
128 all-zero or all-one bits.

| Layout | Q seeds reaching D38E | Maximum selected ROM reads in a 512-cycle seed run | Q=5 controller bits consumed | Selected ROM operands after first input | Candidate output |
| --- | ---: | ---: | ---: | ---: | --- |
| Shared control | 32 | 5 | 128 | 0 | Constant at reached sites |
| Upper pair only | 4 | 6 | 0 | 0 | No reached candidate site |
| Separated pairs | 4 | 61 | 128 | 127 | `39E`/`39F` both `0B` |
| Separated, reversed upper | 32 | 119 | 128 | 127 | `39E`/`39F` both `0B` |

The two separated layouts therefore restore **repeated ROM operand
selection** in a controller-fed path that the shared layout did not show.
That is an architectural distinction worth testing against more of the
photos. It is not yet a carrier or receiver: all 127 post-input ROM reads
per Q=5 run use one address, and the two reached candidate output words hold
`0B` for the real, all-zero and all-one streams. The upper-pair-only layout
does not reach the recurring controller input from Q=5. Q=2 in the separated
layouts has many ROM reads but no controller-input visit in the tested run.
The repeated read is specifically **lower-slice D selection at `38C`** from
Am27S31 address `106`; the [varying-D follow-up](INDEPENDENT-SLICE-D38C.md)
shows that it changes R6 locally but is overwritten before the next loop
boundary. It does not establish an upper-slice D read or a receive filter.

The [report](results/independent-slice-fields.json) records the exact bit
fields, seed counts, ROM addresses, output values, trace digests and source
hashes. The next check is whether a plausible upper instruction bit order
can make the ROM address or a retained state respond to consecutive controller
symbols, while constraining the latch wiring from the photos. No transmitter,
receiver or echo-canceller acceptance criterion is met here.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/independent_slice_fields.py
```
