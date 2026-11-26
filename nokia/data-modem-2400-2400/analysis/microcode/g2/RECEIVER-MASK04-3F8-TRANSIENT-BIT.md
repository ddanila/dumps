# The receive arithmetic exposes a phase bit at `3F8` before the row output loses it

The [state audit](receiver_mask04_collision_state.py) reruns six complete
192,047-cycle real-PROM receive traces at 45° carrier rotation. All six
trace digests and row-pair captures agree with the earlier
[two-visit experiments](RECEIVER-MASK04-TWO-VISIT-PHASE.md). It examines
the 24 symbol instants where row-0/row-3 `3ED` Y is `(F3,F2)` although
the reference waveform has two different phase states.

At ADC visit 47, **all 24 have identical modeled Am2901 Y, Q, all 16 RAM
registers and four flags** at both row-0 and row-3 `3ED`. They are still
identical at visit 94 row 0. No readout of only that modeled instantaneous
state can separate the two labels. At visit 94 row 3, the state splits into
four distinct values with no label conflict. The narrower explanation is
visible earlier in the *same* ADC visit: `3F8` selects different candidate
ADC bytes, and its executed Y and carry separate the labels before the
later row logic erases the distinction.

| Reference phase label at 45° | `3F8` ADC byte at visit 47 | `3F8` Y | `3F8` carry |
| --- | --- | ---: | ---: |
| 0, ten collisions | `03`–`0E` | `0F` | 0 |
| 1, fourteen collisions | `B2`–`B6` | `BF` | 1 |

The previously checked mask-`04` `3F8` instruction pair `D4/C5` forms Y
from the ADC high nibble, R5 and carry, then `3F9` uses `0x100 + Y` as
an Am27S31 lookup address. Thus Y7 is a transient executed arithmetic
result, not a fabricated diagnostic field. In every captured symbol window,
row-0 `3ED` precedes `3F8` by 13 microinstructions and row-3 `3ED`
follows `3F8` by 11. A separate one-bit latch could therefore hold Y7
for a consumer at row 3 under an **assumed** clock and connection.

The [frozen readout](receiver_mask04_3f8_phase_bit.py) keeps the prior
seven-state row-pair table and, only for `(F3,F2)`, uses `3F8` Y7 as
the phase label. It makes 0/72 dibit errors on the six inspected 45°
streams. Frozen before two new random streams, it then gives:

| Carrier rotation | New stream `A431` | New stream `C991` |
| --- | ---: | ---: |
| 45° | 0/12 errors, full coverage | 0/12, full coverage |
| 135° | 0/12, full coverage | 0/12, full coverage |
| 0° | 11/12 unknown | 10/12 unknown |
| 90° | 12/12 unknown | 12/12 unknown |
| 180° | 12/12 unknown | 12/12 unknown |

The 45° streams contain 13 new `(F3,F2)` instances, so their zero-error
result exercises the added bit. At 135° the absolute phase labels differ
by a constant quadrant, which cancels in the differential dibit decision.
The separate earlier nominal Boolean readout still makes 0/72 errors on
the same 0°/90°/180° captures. Neither rule alone is an all-phase receiver;
an executed or photo-compatible way to select or track phase classes is
still needed.

A static search of the four real control PROMs finds no one-, two- or
three-literal raw-output AND that isolates `3F8` among the 20 receive-loop
words. Twenty-eight four-literal choices do; one is
`U10.D1 & U10.D3 & U10.D7 & !U17.D1`. That example also matches 12
other PROM addresses outside the loop, so a real clock would need
mode qualification or tolerance of an extra startup edge. The
[full-trace gate replay](receiver_mask04_3f8_gate_timing.py) finds that
this choice is high at `3F8` exactly 6,000 times and once at startup
`18C`. Its hypothetical NAND rising edge occurs on `3F8→3F9` 6,000
times and once on `18C→3EA`. Every receive edge would capture the
previous `3F8` Y byte; the 6,000-byte edge stream exactly matches the
executed `3F8` stream, including the 16 symbol visits used by the
bit readout. Instruction-level edges do not prove a hazard-free physical
clock. No such gate, Y7 latch, later
phase logic, symbol clock or USART-01 RxD net has been traced. This is a
conditional path through executed microcode, **not a C3 pass** or a
physical wiring claim. The following latch replay tests whether that
edge can preserve Y7 through the later row outputs.

An explicit one-bit latch replay now updates its held value from the
preceding Am2901 Y7 at every candidate NAND edge, including the startup
`18C→3EA` edge. In the 192,047-instruction trace, the startup edge sets
Y7=0 before the first `3ED` observation at cycle 50. Each of the 6,000
`3F8→3F9` edges then supplies the value still held at the next `3ED`
observations: 6,000 each at lags 2 and 10 instructions, and 5,999 each
at lags 18 and 26 because the run stops during its final receive visit.
The row-3 observations at lag 10 on symbol visits 47 and 94 match the
executed `3F8` Y7 for all 16 inspected symbols (32 observations). Lags
18 and 26 belong to the next visit's earlier rows, before its own `3F8`
capture. Thus
the proposed edge has sufficient instruction-level timing to make the
transient bit available throughout the later four-row window. It does
not show that the photographed board actually has this gate, latch or
consumer, or that a symbol-rate circuit retains both visits; those
remain the next C3 tests. The instruction-level model also cannot
exclude combinational clock glitches.

The [state report](results/receiver-mask04-collision-state.json) contains
the full sampled RAM/Q/Y/flags and ADC reads; the
[bit report](results/receiver-mask04-3f8-phase-bit.json) contains all
scores, clock-decode candidates, trace and source hashes. Reproduce from
the microcode directory with
`python3 g2/receiver_mask04_collision_state.py` and
`python3 g2/receiver_mask04_3f8_phase_bit.py`. The
[clock report](results/receiver-mask04-3f8-gate-timing.json) reproduces
with `python3 g2/receiver_mask04_3f8_gate_timing.py`.
