# A four-CD4094 cascade changes the controller frame's apparent byte order

The [DSU3556 photograph](DSU3556-SHIFT-REGISTERS.md) shows four CD4094BE
shift-and-store registers. The executed 8031 interface sends four bytes
and pulses its candidate latch control only after the fourth completes.
An [8051 hardware manual](https://ww1.microchip.com/downloads/aemDocuments/documents/OTH/ProductDocuments/UserGuides/doc4316.pdf)
specifies LSB-first serial mode 0, and the
[CD4094B datasheet](https://www.ti.com/lit/ds/symlink/cd4094b.pdf) identifies
Q1 as the first shift stage and Q8 as the eighth. The four-chip cascade,
chip order, latch strobe and DSP bus are **hypotheses**, not traced nets.

The [32-stage model](photo_cd4094_order.py) shifts all four ROM-executed
controller bytes, then samples the storage outputs. Logical chip 0 is the
chip nearest the serial input. It tests two simple byte-bus orientations:
Q1→D0 through Q8→D7, or Q8→D0 through Q1→D7. For the two main-loop
frame classes and the A0/A1 state frames, the result is:

| Controller SBUF bytes | Logical chips 0→3, Q1→D0 | Logical chips 0→3, Q8→D0 |
| --- | --- | --- |
| `D0 47 A1 22` | `44 85 E2 0B` | `22 A1 47 D0` |
| `D0 42 A1 BA` | `5D 85 42 0B` | `BA A1 42 D0` |
| `80 02 88 7A` (A0/A2) | `5E 11 40 01` | `7A 88 02 80` |
| `80 02 81 7A` (A1) | `5E 81 40 01` | `7A 81 02 80` |

Twenty distinct candidate bytes were each supplied at D127 and run for
3,000 real-PROM microinstructions. Every selected PC129 address obeyed its
phase recurrence; odd bytes entered the second ROM loop, while even bytes
remained in the first. The [machine report](results/photo-cd4094-order.json)
contains each candidate's read count and trace digest.

This materially qualifies the [joined frame/line witness](PHOTO-127-FRAME-LINE-JOINT.md).
Its `47`-enters/`42`-stays split occurs if **logical chip 2 is wired
Q8→D0**. The same chip wired Q1→D0 presents `E2`/`42`, both even, so
neither class enters the second loop. Logical chip 0 wired Q1→D0 presents
`44`/`5D`, creating the *opposite* branch split. For the A0/A1 frames,
chip 1 wired Q8→D0 presents `88`/`81` and preserves the prior
tone-versus-scan candidate; Q1→D0 instead presents `11`/`81`, both odd.
Thus a result that relies on a literal frame lane needs an explicit
CD4094 chip and Q-pin order. No candidate here establishes the actual
board wiring, DAC08 route, line tone or receiver. The two input orders
remain runnable alternatives rather than a reason to block G2.
