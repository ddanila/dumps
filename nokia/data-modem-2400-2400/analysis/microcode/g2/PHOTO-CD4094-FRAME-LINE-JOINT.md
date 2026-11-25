# Shift-register byte order changes the joined frame/line path

The [joined replay](photo_cd4094_frame_line_joint.py) starts with the four
ROM-executed 8031 main-loop frame classes and their real USART-01 bytes. It
shifts each four-byte frame through the candidate four-CD4094 cascade, then
offers one chip's held output byte at D127 under either Q1→D0 or Q8→D0 bit
order. The USART bytes are expanded LSB-first and offered at D12C for eight
loop visits per bit. This is a diagnostic hold, **not** the board's measured
2,400-bit/s timing. The cascade, pin order, D-input routes, q3 mapping,
upper ROM bank and held-I0 fixture are all labelled assumptions.

All 32 real-PROM runs complete 4,200 microinstructions. Every selected
D127/D12C input equals the offered controller value, and every PC129/PC12E
ROM address follows its executed phase recurrence. The table gives the
number of D12C input visits in selector order `00 / 20 / 40 / 60`:

| Logical chip, nearest serial input first | Q1→D0 | Q8→D0 |
| --- | --- | --- |
| 0 | `0 / 0 / 1006 / 1006` — reversed split | `0 / 0 / 0 / 0` |
| 1 | `1014 / 359 / 1014 / 1014` | `818 / 359 / 818 / 818` |
| 2 | `0 / 0 / 0 / 0` | `884 / 359 / 0 / 0` — earlier `47/42` split |
| 3 | `1016 / 359 / 1016 / 1016` | `0 / 0 / 0 / 0` |

The odd D127 bytes enter the second loop, while the even bytes do not. In
selector `20`, each of the four entering routes reaches phase zero on its
359th D12C visit and then waits at `084`; the other 12 entering cases consume
all offered line bits and continue on the explicit idle zero. No case reaches
candidate output words `392` or `39E`. The [machine report](results/photo-cd4094-frame-line-joint.json)
records the actual transformed byte, ROM read counts, wait cycle and trace
digest for every case.

This makes the earlier literal `47/42` joined result conditional on logical
chip 2 wired Q8→D0. A plausible chip-0 reverse-bit route instead selects the
opposite frame classes. None of these control-flow outcomes establishes the
physical chip order, a sustained line-rate modulator, DAC08 input samples, or
receive behavior. Test a qualified or decoded controller input and an output
latch/ROM consumer under explicit timing assumptions; keep the physical
connection open until an independent clue distinguishes the lanes.
