# A8 does not rescue the split-slice 39E output path

The [split-slice byte relay](SPLIT-FRAME-BYTE-RULE.md) repeatedly selects an
Am27S31 operand at `38C`, receives an offered byte at `38E`, and reaches the
candidate output word `39E`. Its A8 bank source is untraced. The
[executable bank screen](split_rom_bank_screen.py) tests four labelled
hypotheses: global A8 low or high, independently combined with A8 low or high
at `38C`. It replays ascending and descending full-byte sweeps and four real
8031 frame streams from the existing controller fixture: 24 runs and 2,816
`39E` visits in all.

All four bank choices preserve the exact output rule
`Y39E[n] = 0x1B + 2 × (D38E[n−1] & 0x70)` after the startup value `FB`.
The selected ROM operand really changes. In the ascending-byte fixture, the
recurring `38C` address and byte are:

| Global A8 | `38C` A8 | Address | ROM byte |
| ---: | ---: | ---: | ---: |
| 0 | 0 | `0C6` | `25` |
| 0 | 1 | `1C6` | `FC` |
| 1 | 0 | `0F6` | `30` |
| 1 | 1 | `1F6` | `05` |

Changing only the `38C` bank also leaves the final PC, Q and RAM identical
for each stream. Changing the global bank changes startup and internal state,
yet the same `39E` byte rule survives. Thus a missing A8 trace cannot explain
the fixed byte-field behavior at this output candidate in the tested loop.
The ROM operand may still matter at another site or under another timing or
field mapping; this screen does not identify the actual A8 driver.

The [report](results/split-rom-bank-screen.json) records the exact scenario,
input/output witnesses, selected ROM addresses and bytes, final states, trace
digests and source hashes. `39E` is an ALU value, not a traced DAC sample.
The next transmitter experiment should seek a retained ROM-dependent value
and a sample latch path, while the receiver and echo-canceller analyses remain
independent avenues.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/split_rom_bank_screen.py
```
