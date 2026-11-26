# The candidate transmitter is an executed R1 phase accumulator

The [ROM-bank differential trace](JOINT-MASK04-TX-ROM-IMPACT.md)
showed that the proposed output bit Y7 is insensitive to the selected
`129` operand bank. This [phase replay](joint_mask04_tx_phase_accumulator.py)
identifies what drives it in the joint mask-`04` mapping. It feeds the
first **18 continuous A4 dibits** from each executed 8031/8251 TxD
stream into the existing, explicitly assumed four-visit D127 pulse
route. Each selector executes 216,256 real-PROM microinstructions.

At every `127` visit after the first, the modeled Am2901 R1 obeys
`R1_new = (R1_previous + D127) mod 256`. At all four words `127–12A`,
**Y7 equals R1 bit 7**. The replay checks the relation on every visit,
not just the proposed DAC sample instants:

| Selector | D127 visits | Consecutive R1 updates checked | Y7/R1-bit-7 checks | Dibit phase-offset errors |
| --- | ---: | ---: | ---: | ---: |
| `40` call | 54,054 | 54,053 | 216,216 | 0/18 |
| `60` answer | 54,054 | 54,053 | 216,216 | 0/18 |

With the assumed 14.4 MHz microcycle and one D127 visit per four
microcycles, the proposed 9,600 Hz latch takes one sample every 375
visits. Constant A1 D127=`88` advances the 8-bit phase by
`375×0x88 mod 256 = 56` per sample, corresponding to 2,100 Hz.
Constant data baseline D127=`B0` advances it by
`375×0xB0 mod 256 = 208`, equivalent to −48 steps/sample or an
1,800 Hz carrier magnitude. The four-visit pulse changes the phase
by these exact quadrant offsets:

| Dibit | Pulse D127 | Extra phase after four visits |
| ---: | ---: | ---: |
| `00` | `B0` | 0° |
| `01` | `A0` | −90° |
| `10` | `80` | +90° |
| `11` | `90` | 180° |

The measured R1 offsets at all 18 symbol ends equal the cumulative
sum of those pulse steps. Call and answer have the same first 15
dibits, then diverge; their sampled Y7 streams have different SHA-256
values. This gives a concrete executed mechanism for the candidate
tone and DPSK phase changes. It also explains why changing the
`129` ROM bank left candidate Y7 unchanged: that output follows the
accumulated D127 phase in this loop. The ROM operand still changes
lower-bit arithmetic and temporary state.

The D127 bit-to-pulse decoder, four-visit qualification, high-slice
links, oscillator-to-microcycle relation, Y7-to-latch-to-DAC08 B1 wire
and analog line route remain photo-compatible hypotheses. The result
therefore strengthens the *how* of the candidate digital transmitter
without passing C2 or establishing a physical line-output stream.
Next constrain the latch clock and Y7/DAC route from the photographed
parts or an independent output-node observation.

The [machine report](results/joint-mask04-tx-phase-accumulator.json)
contains every dibit and symbol-end phase, the first sample values,
trace hashes and source hashes. Reproduce from the microcode directory
with `python3 g2/joint_mask04_tx_phase_accumulator.py`.
