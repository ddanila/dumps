# The candidate ADC loop depends on an unresolved computed-call index

The sustained `D3F8` receive experiments use the real `3EA–3EE` control
PROM words, but their base scenario supplies **constant index 2** to the
computed BSR at `3EC`. That selects the `3F7–3FA` table row on every pass.
The physical source of the Am8X02 B-input index is untraced, so repeating
that row is a fixture assumption rather than a recovered receive schedule.

The [dispatch-source screen](receiver_dispatch_source_screen.py) keeps the
joint upper-source field map, Q=5, zero RAM and inverted-previous-sign
condition. It executes 16,047 real-PROM microinstructions with held ADC
byte `09` or `59`, trying constant indices 0–3 and modeled Y, Q and
previous-Y as the `3EC` index. The table shows `D3F8` visits for `09` / `59`:

| `3EC` index source | Table rows selected | `D3F8` visits (`09` / `59`) | Result |
| --- | --- | ---: | --- |
| Constant 0 | `3EF` | 0 / 0 | Different eight-word loop |
| Constant 1 | `3F3` | 0 / 0 | Reaches `084` after one dispatch |
| **Constant 2 (prior fixture)** | `3F7` | **2,000 / 2,000** | Repeats ADC row |
| Constant 3 | `3FB` | 0 / 0 | Reaches `084` after one dispatch |
| Current Y | `3EF` | 0 / 0 | Y modulo 4 is 0 in this fixture |
| Current Q | `3F7`, `3F3` | 1,001 / 1 | `59` leaves the ADC path after one read |
| Previous Y | `3EF` | 0 / 0 | Previous Y modulo 4 is 0 |

The constant-2 controls each make 2,001 dispatches: one precedes the first
ADC visit, then one occurs per loop pass. Under Q-derived dispatch, the first
index is 2. With `59` at `D3F8`, the next Q index is 1 and the path reaches
`084`; with `09`, indices 1 and 2 alternate while the ADC row is visited
1,001 times. Thus a datapath-derived index can make ADC value affect the
**choice of subsequent microcode row**, but it does not sustain the tested
`59` input under this mapping and seed.

Two reference waveforms make the same point without holding a diagnostic
byte. The first 128 complementary ADC codes from dibit patterns `0,1,3,2`
and `0,0,0,0` contain 50 and 9 distinct values, respectively. Constant
index 2 completes all **24,000** offered visits on each waveform. Q-derived
dispatch reads only the first byte (`00`) once and reaches `084` on both.
The first waveform's `59` is its **second** sample, so that Q run never
reaches it. This rejects Q as a sustaining index source for these reference
streams under the tested startup state; it does not identify the actual
board source.

## A two-row index schedule survives

The board photograph identifies a 74LS161 counter at U24 and a U9 B3 track
fragment toward the U4 buffer, but neither establishes their connection to
the computed-call index. As a **counter-like diagnostic**, the screen tries
all four start phases of the complete `0→1→2→3` and reverse cycles. Every
one reaches `084` after at most two dispatches under held `09` or `59`.
It then tries alternating `0/2` and `1/2` row pairs in both phases.
The `1/2` pairs exit immediately. Both `0/2` phases sustain **1,000 ADC
visits** in the 16,047-instruction held-byte run, and the ALU selects the
offered byte at every one of those visits for either `09` or `59`.

With a 128-sample reference waveform, `0/2` and `2/0` each complete
**12,000 ADC visits** and 24,001 dispatches in 192,047 instructions for both
`0,1,3,2` and `0,0,0,0` dibit patterns. The ADC hold is adjusted to
`94,94,94,93` visits per four samples because this path reaches `D3F8`
once per two eight-instruction dispatch loops. The 14.4 MHz oscillator and
one-microinstruction-per-period assumption would make that 1,500
instructions per 9,600-Hz sample; the actual divider and ADC conversion
clock are not established.

A paired 32-sample detailed replay of the `0/2` path selects all **3,000**
offered ADC bytes and performs 3,000 `3F9` Am27S31 lookups per waveform.
The two runs have the same PC path, but **2,781/3,000** lookup addresses
differ. That is a conditional ADC→state→ROM response with an interleaved
second table row, stronger than the constant-index-2 liveness result. It is
still not a recovered modem receiver: `0/2` timing, counter/buffer wiring,
sample coding and any output-to-USART route are hypotheses, and no dibit
decision has been found on this path.

This matters for C3/C4: the existing long ADC, decision and echo screens
are valid **conditional constant-index-2** executions, not evidence that the
board continuously runs that row in a call. A physical index could come
from a latch, external buffer or another datapath value. The modeled Y/Q
options are diagnostic hypotheses, not recovered Am8X02 wiring. The next
receiver experiment should constrain the B-input source from the visible U4
buffer and data-flow timing, then test whether the surviving `0/2` schedule
produces a generalizing receive decision and an explicit output/USART route.

The [machine report](results/receiver-dispatch-source-screen.json) includes
every dispatch-entry count, first twelve events, final PC, trace digest and
source hash. Reproduce it with:

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/receiver_dispatch_source_screen.py
```
