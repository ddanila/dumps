# Held D3F8 low nibble selects a periodic ROM state machine

The [read-valid PROM-data route](LOWER-I-PROM-DATA-ROUTE.md) carries the
`3F7` Am27S31 byte into later arithmetic and a branch under an untraced
I7/A0 and I0/A1 source mapping. The [held-byte screen](lower_i_held_nibble_cycles.py)
runs all 256 bytes at the selected D3F8 input site with Q=`05`, zero RAM,
the real four-PROM store and Am27S31 dump. It then traces the sustained
low-nibble classes for 1,580 microinstructions each.

All 16 choices of a byte's **high nibble** give the same full modeled trace
for a given low nibble. Ten low-nibble values keep the `3ED–3FA` loop active;
six exit through `1E9` or `1EA` in the 512-cycle screen. Each sustained
class settles into an exact repeating ROM-address, ROM-byte and ALU Y
sequence at `3F8`, `3F9` and `3FA`:

| D3F8 low nibble | Settled period in `3F7` visits | Zero-based settled start visit |
| ---: | ---: | ---: |
| `1` | 8 | 3 |
| `2` | 9 | 2 |
| `3` | 7 | 14 |
| `4` | 2 | 1 |
| `5` | 3 | 3 |
| `7` | 7 | 11 |
| `8` | 2 | 4 |
| `9` | 12 | 4 |
| `C` | 21 | 6 |
| `F` | 12 | 2 |

Each reported period repeats at least four times through the end of the
trace. The other low nibbles are `0`, `6`, `A`, `B`, `D` and `E`. This is a
concrete low-nibble-controlled recurrent computation in the emulator. Its
ROM address sequence changes with the held input and the ROM bytes reach
ALU arithmetic; it is a stronger algorithmic lead than a transient ROM
read. The sequences are not yet DAC samples. Their physical frequency
cannot be inferred without the microcycle divider and latch clock.

The [report](results/lower-i-held-nibble-cycles.json) contains the 256-byte
digest equivalence test, branch outcomes, each exact period and its ROM/ALU
values. The D3F8 source, paired PROM-data-to-latch wiring, inversions and
capture timing are hypotheses. A changing controller stream still needs a
valid route through this state machine and a measured or constrained output
continuation.
