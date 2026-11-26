# The ROM-sensitive `12A` byte requires settled-data latch timing

The [paired raw-edge replay](joint_mask04_tx_bank_edge_timing.py) runs the
joint receive/transmit mapping for 4,096 real-PROM words with the same
held `D127=88` tone input, changing only Am27S31 A8 at `129`. U10 D2
has the reached level sequence `0,0,1,0` across `127–12A`: it rises
as `129` is fetched and falls as `12A` is fetched. A 74LS273 responds
to a rising CLK edge, so a direct D2 clock and an inverted D2 clock
are distinct, photo-compatible timing hypotheses.

| Raw edge | Y before the new word settles | Bank-different pre-edge bytes | Bank-different settled bytes |
| --- | --- | ---: | ---: |
| D2 rise at `129` | `128` Y | 0/1,014 | 0/1,014 at `129` |
| D2 fall at `12A` | `129` Y | 0/1,014 | **221/1,014 at `12A`** |

Every changed settled `12A` byte differs only in bit 0. A direct
rising-edge latch that captures prior `128` Y, or an inverter-assisted
falling-edge latch that captures prior `129` Y, therefore misses this
ROM-bank effect in the held-tone trace. To see the candidate bytes from
the [full controller-fed phase screen](JOINT-MASK04-TX-BANK-PHASE.md),
the data at `12A` must settle before the selected latch edge. That could
come from a later clock phase or a suitable delay/hold circuit; the
available photos do not establish either route. The full-stream replay
shows that once settled `12A` Y is sampled, all 375 divided-clock phases
eventually contain changed bytes on both selectors.

This is a timing requirement for the ROM-sensitive **candidate** DAC
stream, not proof of a physical clock or Y-to-74LS273 connection. In
particular, the raw PROM transition and the ALU output can race in a
real board, and the current model does not resolve propagation delays
or setup/hold time. The photo-suggested 74LS273 Q4→DAC08 B5 segment
remains only one part of the output bus. C2 stays open; test an explicit
post-`12A` capture mechanism or constrain CLK/data on the board while
continuing other runnable C2/C3 paths.

The [machine report](results/joint-mask04-tx-bank-edge-timing.json)
contains both real-PROM trace hashes, raw-edge counts and byte-difference
masks. Reproduce from this directory with
`python3 g2/joint_mask04_tx_bank_edge_timing.py`.
