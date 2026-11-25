# AF→B0 frame bits discriminate two candidate DSC input routes

The [executed zero-run transition](ZERO-RUN-DETECTOR.md) changes the 8031's
four-byte frame from `D0 42 89 9A` at `AF` to `D0 42 81 1A` at `B0`.
The [route screen](photo_af_b0_frame_routes.py) offers those exact frames to
two earlier photo-compatible DSC hypotheses. The controller bytes are ROM
outputs; the CD4094 cascade, bit order, DSP ingress and timing remain
assumptions.

At the candidate `D38E` input, one frame byte is held for 16 visits, followed
by its `B0` counterpart for 16 visits. All four real-PROM runs complete. The
reached `39E` ALU Y is unchanged across the transition:

| Frame byte lane | `AF→B0` | Settled `Y39E` |
| --- | --- | --- |
| 0 | `D0→D0` | `BB→BB` |
| 1 | `42→42` | `9B→9B` |
| 2 | `89→81` | `1B→1B` |
| 3 | `9A→1A` | `3B→3B` |

The independently established byte rule explains this negative result:
`Y39E[n] = 1B + 2×(D38E[n−1] AND 70)`, modulo 256. The changed bits lie
outside mask `70`; the selected Am27S31 address stays `1F6`. Thus this
specific reached relay cannot carry the `AF→B0` control change at `Y39E`.
Other instructions or input routes are not ruled out.

A separate q3 experiment holds each candidate CD4094 byte at `D127` for
3,000 real-PROM instructions. Logical chip 0 is nearest the serial input;
both Q1→D0 and Q8→D0 byte orders are tested. Four of eight routes change the
executed trace, exactly those where the held byte changes:

| Logical chip | Q1→D0 `AF→B0` / PC129 reads | Q8→D0 `AF→B0` / PC129 reads |
| --- | --- | --- |
| 0 | `59→58` / `69→740` | `9A→1A` / `740→740` |
| 1 | `91→81` / `173→125` | `89→81` / `213→125` |
| 2 | `42→42` / `740→740` | `42→42` / `740→740` |
| 3 | `0B→0B` / `23→23` | `D0→D0` / `740→740` |

Chip 0 in Q8→D0 order changes its phase-step value even though the PC129
read count is unchanged. The result makes the two frame bits useful as a
discriminating input stimulus, but it does not identify a command meaning,
an echo-canceller enable, or the physical DSC connection. Each `D127` case
is a separate held-byte startup run; a continuous transition and echo
residual test are still needed for C4. The [machine report](results/photo-af-b0-frame-routes.json)
records traces, fixture choices and source hashes.
