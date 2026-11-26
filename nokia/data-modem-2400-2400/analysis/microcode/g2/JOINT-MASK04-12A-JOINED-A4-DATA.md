# A4 training and fresh data stay decodable in one sustained DSC line replay

The [A4-only phase test](JOINT-MASK04-12A-A4-PHASE-TRAINING.md)
trained the receive-state map in one DSC run and applied it to separate
saved payload runs. This experiment removes that gap in the DSC line
model. In each selector mode, it offers the exact 64-bit V.26 ter
segment-2 A4 window previously verified in the unchanged 8031 output,
followed immediately by eight fresh scrambled data bytes. The
transmitter executes the real q3/mask-04 PROM continuously across all
64 A4-plus-data dibits; its sampled `12A` line is filtered and fed to
one sustained real-PROM receiver execution. The same one-time `20` R1
offset at the start of the muted interval tests the half-quadrant
carrier start.

| Selector | Known A4 line bytes | Fresh data line bytes | Exact A4-trained maps | Following unseen data |
| --- | --- | --- | ---: | --- |
| `40` | `FC 03 7C 0E 0E F8 C0 18` | `D1 EE 96 B4 F9 33 80 C6` | 1/64 | 32/32 dibits, eight exact line bytes |
| `60` | `FC 03 7C CE 07 E1 84 EC` | `CF 17 E6 01 D3 1B BF 9A` | 1/64 | 32/32 dibits, eight exact line bytes |

In both runs the executed receiver's captured state family is
`2,6,9,D`. The known A4 transitions alone select the same unique map
`2→0, 6→3, 9→1, D→2`, anchored at state `2`. It makes no errors on the
following payload dibits and reconstructs the offered data bytes.
No payload labels enter the map selection. The independent fixed-carrier
reference decoder makes three errors per joined stream; those errors
are not used in the DSC decision or map fit.

This is a conditional continuous **DSC** transmit/receive witness.
The 16-byte line stream joins a controller-verified A4 window to
scrambled payload bytes generated from a separately initialized
controller fixture; it is not an uninterrupted 8031 A4-to-data
session. The data-symbol pipeline, R1 phase intervention, DAC bus,
analog filter, ADC input, capture phases and external quadrant logic
are still explicit hypotheses. A separate 16-byte USART/8031 handoff
was not modeled here. C2/C3 remain open pending a photo-compatible
phase-selection and serial circuit and a continuous controller stream.
The unknown wiring is an active assumption, not a goal blocker.

The [machine report](results/joint-mask04-12a-joined-a4-data.json)
records real-PROM trace digests, line/ADC hashes, known A4 bytes,
phase-state candidates and held-out data results. Reproduce from the
microcode directory with:

```sh
python3 g2/joint_mask04_12a_joined_a4_data.py
```
