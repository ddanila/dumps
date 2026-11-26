# Controller dibits appear as phase steps in executed DAC-MSB candidates

The [segment-1 phase replay](JOINT-MASK04-MSB-SEGMENT1-PHASE.md) measures
180° A3 reversals directly in the candidate DAC MSB. This
[replay](joint_mask04_msb_data_phase.py) checks the next C2 requirement:
whether A4 data phase steps follow the controller's transmitted dibits,
without using an assumed analog bandpass or the reference receiver.

It executes the same fixed lower-mask-`04` mapping for **1,248,256 real-PROM
instructions per call/answer selector**, with controller-derived A1–A4
inputs. The complete trace and candidate sample hashes match the earlier
free-clock and segment-1 runs. The controller's first nine line-side TxD
bytes supply the 32 A4 dibits; the existing sequence check verifies that
they contain the V.26 ter segment-2 pattern.

For each of four free-clock phases `127`–`12A`, the script forms an
1,800 Hz complex phasor from each symbol's eight **raw MSB** samples. It
compares the phase change from the final A3 symbol to the first A4 symbol
and all 31 A4-to-A4 changes with the quadrants predicted by the frozen
four-visit D127 input rule. That rule has a negative phase sign; the
opposite sign is a control.

| Selector | Direct A4 phase steps | Wrong quadrants with frozen sign | Largest phase error | Wrong quadrants with opposite sign |
| --- | ---: | ---: | ---: | ---: |
| Call `40` | 32 | **0** | 40.29° | 6 |
| Answer `60` | 32 | **0** | 40.29° | 8 |

The four capture phases give the same MSB bitstream within each selector,
so this is **64 distinct data-step comparisons**, not 256 independent
ones. Full-byte captures still differ by phase. The 40.29° maximum is
below the 45° nearest-quadrant boundary; the report includes every
observed and predicted angle and a compact copy of the executed MSB
sample bits.

Together with the A1 tone and A3 half-turn tests, this shows the
candidate DSC output bit carries the controller's tone, segment-1
reversals and segment-2 dibit phase changes in one uninterrupted PROM
run. The D127 four-visit rule, Y7→sample latch→DAC08 B1/pin 5 route,
sample clock, DAC current output and analog line path remain labelled
assumptions. The controller TxD bytes are executed but projected onto the
DSC timebase. This is strong **digital transmitter evidence**, not a
physical line-output identification or a C2 pass. A photo-compatible
B1/latch/analog route or an independent output-node constraint is the
next useful test; unknown continuity does not block it.

The [machine report](results/joint-mask04-msb-data-phase.json) includes
the 64 unique comparisons, four capture-phase checks per selector,
source hashes and the packed candidate MSB sample streams. Reproduce
from the microcode directory with
`python3 g2/joint_mask04_msb_data_phase.py`.
