# The two candidate tone and carrier swaps cannot be one fixed byte wiring

The [A1 tone-state candidate](PHOTO-CD4094-BIT-SWAP-TONE.md) crosses
CD4094 chip-1 D0/D3, turning the ROM-executed A1 state byte `81→88`.
The [main-frame carrier candidate](PHOTO-MAIN-FRAME-CARRIER-SWAP.md) instead
crosses D0/D4, turning every main-loop frame's chip-1 byte `A1→B0`.
Both are useful **separate** experiments, but a single static chip-1 bus
cannot implement both crossings. The [compatibility replay](photo_state_data_bus_compatibility.py)
checks that conflict against the actual controller frames and real PROMs.

The raw bytes `81` and `A1` differ in **one bit**. Any fixed one-to-one
permutation of their eight wires, with any fixed per-bit inversions, keeps
their Hamming distance at one. At the hypothetical 9,600-sample/s gate, the
exact phase-step equations give the following required D127 byte sets:

| Oscillator periods per microinstruction | 2,100 Hz A1 step | 1,800 Hz main-data step |
| ---: | --- | --- |
| 1 | `78` or `88` | `50` or `B0` |
| 3 | `68` or `98` | `10` or `F0` |

Every tone/data pair from those sets differs in **at least two bits**, even
when the two modes use different tested divisors. Thus no fixed bit
permutation plus fixed inversion can map the same chip-1 byte lane to both
required steps under this model. This is a wiring-class constraint, not a
claim that the physical modem lacks either function.

The runner also executes both candidate crossings in **both** modes for
3,000 real-PROM microinstructions each, using upper-bank q3 and the same
photo-B5-compatible minimal full-byte DAC hypothesis:

| Fixed crossing | A1 state D127 / full-code peak | Main-frame D127 / full-code peak |
| --- | --- | --- |
| D0/D3 | `88` / **2,100 Hz** | `A8` / 900 Hz |
| D0/D4 | `90` / 600 Hz | `B0` / **1,800 Hz** |

All four runs stay in the `127–12A` loop for 740 selected PC129 reads, and
every address and ALU Y follows the executed ROM recurrence. The 640-sample
projections are invariant up to rotation across all start phases. The
[machine report](results/photo-state-data-bus-compatibility.json) includes
the exact-step sets, Hamming distances, four trace digests and output peaks.

This means the two attractive separate spectra **cannot be combined into
one fixed chip-1-to-D127 pin permutation**. A state-dependent mux or logic
decode, another CD4094 chip, a different sample clock or an output path
outside this q3 loop remains runnable. The A1=2,100 Hz and main=1,800 Hz
state labels themselves are still protocol hypotheses; the actual board
wiring and DAC clock are untraced. Next use the other controller frame bytes
and observed mode signals to constrain a possible mode-select circuit,
rather than treating either crossing as the recovered Nokia wiring.
The [preserved-chain decode check](PHOTO-CONTROLLER-MODE-DECODE.md) adds a
fixture caveat: the chain emits `A1` during A1, so the `81` source in this
Hamming comparison is not present in every executed A1 run.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/photo_state_data_bus_compatibility.py
```
