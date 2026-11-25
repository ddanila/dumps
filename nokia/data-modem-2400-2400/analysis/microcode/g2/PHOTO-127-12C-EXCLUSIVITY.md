# This D127 input alternative does not drive the PC12C table loop

The [execution screen](photo_127_12c_exclusivity.py) tests a specific
alternative to the fixed [q1/q2 ROM-feedback run](photo_variant_rom_loop.py):
the first fitted ROM gate still selects PC12C, but does **not** select PC127.
This lets a scenario byte enter D at PC127. The gate change, q1/q2 A-field
choices and D127 source are hypotheses, not traced board connections. Both
mappings run the real control PROMs and Am27S31 dump from Q=0 and zero RAM.

Across all 256 held D127 bytes, in 512 microinstructions per run:

| Mapping | Bytes that enter PC12C ROM feedback | Other bytes | PC392 visits |
| --- | --- | ---: | ---: |
| q1 | `00` | 255 revisit PC127 | 0 |
| q2 | `00`, `77`, `B7`, `B8`, `B9` | 251 revisit PC127 | 0 |

The entered runs make one PC127 read and 116 PC12C visits; the others make
118 PC127 reads and no PC12C visits. This is a control-flow split, not a
stream of controller-selected table addresses.

The actual 128-bit 8031 scrambler fixture starts with `0`, so both mappings
consume **one** bit and then make 500 PC12C ROM reads in a 2,048-cycle run.
Reversing that bitstream diagnostically begins `1,1,1,1,1,0`: both mappings
consume those six bits and then make 495 ROM reads. In either order the
PC12C address sequence after entry is the same fixed sequence for that
mapping, and neither run visits candidate output word `392`.

Thus this externally driven PC127 alternative cannot be used as evidence
that the smooth `16F–1CF` ROM region is a controller-driven pulse filter or
that these runs transmit data. Another gate, state fixture, mapping or input
route may behave differently; the result closes only this candidate. The
[report](results/photo-127-12c-exclusivity.json) records the full-byte
classification, controller-stream traces, source hashes and exact fixture.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/photo_127_12c_exclusivity.py
```
