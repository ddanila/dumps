# Conditional ADC-to-ROM lookup in the D3F8 loop

The [upper-D candidate](LOWER-I-D3F8-UPPER-D-ROUTE.md) now has an
instruction-level explanation. In the executed real-PROM trace, the loop
repeats `3F8 → 3F9 → 3FA → 3ED → 3EA → 3EB → 3EC → 3F7 → 3F8`.
At `3F8`, the lower Am2901 instruction is `D6` and the candidate upper
instruction is `FD`. The upper slice computes an XNOR of the assumed ADC
byte's high nibble and the pre-instruction high nibble of RAM[A]. Its upper
Y nibble is therefore `(~(D[7:4] ^ RAM[A][7:4])) & 0xF`. The next instruction,
`3F9`, selects the actual Am27S31 byte at address `0x100 + Y` from `3F8`.
That is a direct sample-and-state to lookup-table path in this mapping.

The [reproducible trace check](lower_i_d3f8_lookup_chain.py) verifies the
ALU equation, consecutive PCs, address equation and byte against the dumped
512-byte PROM on **every one of 512 D3F8 visits** for each of two reference
waveforms. It also runs the same full bytes with bits 4–7 masked, under the
baseline `FC` and candidate `FD` upper instructions. The full and masked
runs follow identical PC paths in each pair.

| Reference dibits | Baseline `FC`: differing next `3F9` addresses | Candidate `FD`: differing next `3F9` addresses |
| --- | ---: | ---: |
| `0,1,3,2` | 0/512 | 324/512 |
| `0,0,0,0` | 0/512 | 324/512 |

For the first waveform, the first changed held sample occurs at visit 188:
full D=`59`, pre-RAM[A] high=`0` gives Y=`A7`, so `3F9` reads PROM address
`1A7` (`0B`). Masking the same sample to D=`09` gives Y=`F7`, so it reads
`1F7` (`07`). In the baseline, upper instruction `FC` uses zero in place
of external high D, and all 512 next addresses are identical across that
full/masked pair. The [saved report](results/lower-i-d3f8-lookup-chain.json)
contains both waveforms, first differences, trace digests and source hashes.

The U17 bit 6 → U8 I0 instruction connection, ADC input bus, sample clock
and condition mux are still hypotheses. This result identifies how the
candidate microprogram consumes high ADC bits and uses the ROM, but it does
not identify a dibit decision or a path to USART RxD. The next test should
follow the `3F9` table value through the remaining loop instructions and
test a decision that generalizes across held-out input streams.
