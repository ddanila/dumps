# A held controller frame byte gives a held DSC output in the candidate loop

The [DSU 3556 photo](DSU3556-SHIFT-REGISTERS.md) shows four CD4094BE
shift-and-store registers, a plausible 32-bit parallel destination for the
8031's four-byte serial send. As a more direct control-path hypothesis than
offering four bytes sequentially to the DSC, the
[latched-frame screen](photo_latched_frame.py) holds one selected byte lane
from the fourth executed [controller frame](RECEIVED-CHAIN.md) at DSC input
word `38E` for 128 visits. It tests all four byte lanes for each of the four
received-selector classes: 16 real-PROM runs under the separated-slice,
independent upper-B candidate.

| Received selector | Fourth controller frame | Settled `39E` ALU Y for lanes 0, 1, 2, 3 |
| --- | --- | --- |
| `00` | `D0 42 81 EA` | `BB 9B 1B DB` |
| `01` | `C0 42 81 EA` | `9B 9B 1B DB` |
| `40` | `D0 42 81 BA` | `BB 9B 1B 7B` |
| `41` | `C0 42 81 BA` | `9B 9B 1B 7B` |

Every run selects the held byte on all 128 visits and reads Am27S31 address
`1F6` after startup. Its reached `39E` value starts at `FB`, then remains
at the tabled code for the other 127 visits. This matches the exact
[byte-field rule](SPLIT-FRAME-BYTE-RULE.md): a held input produces a held
output, even when the controller frame class changes its level. Swapping or
inverting fixed output bits would change the code, but cannot create a
carrier in this loop without a changing source or a different path.

The [report](results/photo-latched-frame.json) records all 16 byte-lane
choices, output values, ROM addresses, trace digests and source hashes.
The CD4094 cascade, latch strobe, output-to-DSC route and byte order are
untraced; this is a labelled hypothesis. `39E` is not a traced DAC sample.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/photo_latched_frame.py
```
