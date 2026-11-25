# Candidate ADC impulses do not leave persistent state in the 389–3A1 loop

The [earlier D-site screen](INDEPENDENT-SLICE-INPUT-SITES.md) checked one
initial Q seed. The [Q-seed retention screen](receiver_seed_retention.py)
extends its one-byte impulse test to all 256 initial Q values in three
real-PROM layouts: separated slice fields, reversed upper fields, and a
photo-compatible independent upper-B field. In each layout, the candidate
external D-input site is one that the executed Am2901 instruction selects:
`38E` in the first and third layouts, `3A1` in the reversed layout. For the
`3A1` case, the existing controller bitstream remains at `38E`. For the two
`38E` cases, the candidate ADC impulse replaces that controller stream.

The program receives zero at the candidate site except for input visit 20,
where it receives `01`, `10`, `40`, `80` or `FF`. Each run executes 1,024
microinstructions. It compares the full modeled final state against an
otherwise identical zero-input run. Only Q seeds with at least 23 visits to
the candidate site can test two or more loop iterations after the impulse.

| Layout | Eligible Q seeds | Input visits per eligible run | Seeds retaining any tested impulse at cycle 1,024 | Q=5 boundaries changed by `FF` |
| --- | ---: | ---: | ---: | --- |
| Separated | 32 | 82 | 0 | 20 |
| Reversed upper | 32 | 81 | 0 | 20 |
| Independent upper B | 24 | 82 | 0 | 20, 21 |

The Q=5 trace verifies that the `FF` byte is actually selected by the ALU.
The independent upper-B candidate carries its effect one boundary longer,
consistent with its [one-visit byte relay](SPLIT-FRAME-BYTE-RULE.md), but all
five byte probes converge by the end of each eligible run. This narrows these
specific candidate receiver routes: none supplies a retained phase or filter
state under the tested timing and startup assumptions. It does not exclude
another branch, input source, ADC polarity or output path, and it does not
demonstrate recovered bits.

The [report](results/receiver-seed-retention.json) contains the eligible Q
seeds, visit counts, retained-state comparisons, trace witnesses and source
hashes. The physical ADC-to-D route remains untraced.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/receiver_seed_retention.py
```
