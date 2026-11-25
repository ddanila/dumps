# Preserved controller A1 frames defeat a simple state-to-tone decode

The [joint bus constraint](PHOTO-STATE-DATA-BUS-COMPATIBILITY.md) showed that
the isolated A1-state `81` and main-data `A1` bytes cannot become the
proposed 2,100/1,800 Hz phase steps through one fixed bit permutation. The
[logic-decode replay](photo_controller_mode_decode.py) tests a small
alternative using the candidate logical CD4094 chip-1 Q8→D0 byte:

```text
capture-enable = raw bit 0
mode = raw bit 5
D127 bits 7,5,4,3 = 1, mode, mode, NOT mode; other bits = 0
```

This uses fan-out and one inversion rather than an eight-bit mux. The DSC
photo identifies a 74LS04 inverter (U13) and 74LS244 buffer (U4), but **no
net from either part to these candidate bits is traced**. The LS273 capture
qualification, 9,600 Hz clock, upper ROM bank, q3 mapping and full DAC bus
are also hypotheses.

| Controller source | Chip-1 byte | Enable / mode | D127 | Projected full-code peak when captured |
| --- | ---: | ---: | ---: | ---: |
| Isolated A0 send | `88` | 0 / 0 | `88` | no hypothetical capture |
| Isolated A1 send | `81` | 1 / 0 | `88` | 2,100 Hz |
| Isolated A2 send | `88` | 0 / 0 | `88` | no hypothetical capture |
| Four main-loop first-line frame classes | `A1` | 1 / 1 | `B0` | 1,800 Hz |
| **Preserved-chain A1 sends** | **`A1`** | **1 / 1** | **`B0`** | **1,800 Hz** |
| Preserved-chain A2 sends | `A8` | 0 / 1 | `B0` | no hypothetical capture |

The first four rows look like a possible tone/data selector. The last two
are the necessary check: across all 256 selector runs in the uninterrupted
8031 main-loop fixture, **all 512 A1 sends carry `80 02 A1 7A`**, while all
512 A2 sends carry `80 02 A8 7A`. The isolated state-send fixture instead
provided `80 02 81 7A` for A1. [The controller's third-byte builder](../../controller/OUTPUT32.md)
identifies bit 5 as a **counter-phase flag**, not a state-only tone/data bit.
Thus the same A1 state can yield different candidate chip-1 bytes under the
two executed fixtures. The main-loop fixture preserves controller RAM across
iterations but uses synthetic receive events and forced timer underflow; it
does not represent a full natural-duration call. The A1=2,100 Hz command
interpretation remains provisional.

All nine distinct source/mode replays execute 3,000 real-PROM
microinstructions cleanly. Every run selects 740 upper-bank PC129 values and
matches the phase/ROM/Y recurrence. The hypothesized LS273 full-code stream
is projected at one capture per 375 visits; the 2,100 Hz isolated-A1 code
puts 0.336 of its variance in that bin and the 1,800 Hz main/chain-A1 code
puts 0.604 there. Suppressing captures for A0/A2 is an external gate
assumption, not a measured analog silence. The
[machine report](results/photo-controller-mode-decode.json) records the
controller-frame counts, nine trace digests, projections and source hashes.

This fixed decode **cannot be promoted as a state-to-tone explanation** from
the isolated A1 result. A later counter phase in A1, another frame bit,
mode-dependent logic, or an entirely different DAC path could still be
responsible. Next test how controller output32 bit 5 evolves over a realistic
A1 interval and which frame signals persist across the A1→A2→data transition;
do not block on untraced nets or assume the first isolated A1 frame is the
physical tone command.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/photo_controller_mode_decode.py
```
