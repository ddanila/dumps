# No literal A3 frame byte at D127 supplies segment-1 reversals

The [interrupt-paced controller run](MAIN-LOOP-TIMER1-SEGMENT2.md) places A3
before the exact V.26 ter segment-2 byte pattern and records **no port-01
writes during A3**. Its nonempty four-byte frames contain six distinct byte
values: `D0`, `42`, `81`, `A1`, `C1` and `BA`. This
[screen](photo_a3_held_frame_segment1.py) tests the narrow, photo-compatible
hypothesis that one CD4094 frame-byte lane is held directly at the candidate
DSC2847 D127 input, with no symbol-rate data pulses.

The three even bytes `42`, `BA` and `D0` each sustain the q3 PC127/PC129
loop for 32 symbols. Each run executes **384,256 microinstructions** and
checks **96,054** selected PC129 PROM addresses, bytes and ALU Y values.
Against the unmodulated D127=`B0` carrier, their first eight symbol-end
phase offsets are:

| Held D127 | First eight relative phase offsets, in 256-step units | First symbol's eight sample offsets |
| --- | --- | --- |
| `42` | `240 224 208 192 176 160 144 128` | `146 112 78 44 10 232 198 164` |
| `BA` | `48 96 144 192 240 32 80 128` | `10 176 86 252 162 72 238 148` |
| `D0` | `0 0 0 0 0 0 0 0` | `32 0 224 192 160 128 96 64` |

Segment 1 requires `128, 0, 128, 0, …` **relative to the carrier** at
successive symbols, then a retained offset within each symbol. None of the
three held bytes has that trajectory. `D0` is a useful alias trap: its phase
returns to zero offset at every symbol boundary but drifts throughout each
symbol, so a boundary-only comparison would miss the frequency change.

The other three A3 bytes are odd. The previous
[all-byte PROM execution](PHOTO-127-PARITY-EXIT.md) shows that literal held
`C1`, `81` and `A1` leave the PC127 loop after respectively 61, 125 and
221 PC129 reads, far short of 32 symbols. Their later behavior depends on
the separately assumed D12C input and is not excluded here.

This closes **one literal, held frame-byte-to-D127 segment-1 route** under
the stated q3 mapping and 3,000-visit symbol schedule. It does not rule out
a decoded frame command, a symbol-rate idle pattern supplied by another
circuit, or an autonomous different microcode loop. The CD4094 lane, D127
connection and DAC sampling remain untraced. The
[machine report](results/photo-a3-held-frame-segment1.json) retains the
phase checkpoints, DAC-code digests, trace digests and source hashes.
