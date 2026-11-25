# A row-3 bit gate preserves one differential dibit parity across input levels

The [row-pair phase code](RECEIVER-MASK04-ROWPAIR-PHASE-CODE.md) decoded
both dibit bits at one reference level but its eight-state lookup failed
after a [gain change](RECEIVER-MASK04-ROWPAIR-LEVEL-CHECK.md). Examining the
executed `3ED` Y bytes gives a smaller, fixed candidate readout:

```text
state[k] = OR(Y_row3[k].bit0, Y_row3[k].bit1, Y_row3[k].bit2)
decision[k] = state[k] XOR state[k-1]
target[k] = dibit[k].bit0 XOR dibit[k].bit1
```

Here `k` is a 1,200-baud symbol boundary. The fixed row-3 byte is captured
under the same labelled mask-`04`, four-row, complementary-ADC and proposed
PROM/NAND latch fixture. The two-input XOR is **external diagnostic logic**;
the DSC execution supplies the byte, not an identified USART bit. The
target follows from the reference differential phase steps: dibits `00`
and `11` change phase by an even quadrant count, while `01` and `10`
change it by an odd count. The 1,800 Hz carrier's 180° advance is even and
does not affect this parity.

The [gate replay](receiver_mask04_row3_parity_gate.py) checks ten previously
saved full-PROM traces, then runs six **new 192,047-instruction real-PROM**
traces on two fresh random streams at each of nominal gain, 0.75 gain and
+16 PCM bias. It freezes the gate before those six runs. Every reference
waveform is independently decodable.

| Source of executed row-3 byte | Transitions | Gate errors | Same gate on raw ADC errors |
| --- | ---: | ---: | ---: |
| Earlier changed-level and gain-adaptation traces | 120 | **0** | 64 |
| Six fresh full-PROM traces | 72 | **0** | 39 |
| **Total** | **192** | **0** | **103** |

The previously saved 0.75- and 1.25-gain runs also support a
[gain-specific phase-code experiment](receiver_mask04_rowpair_gain_adaptation.py).
Freezing a new seven-state codebook from one periodic and one random stream
at 0.75 gain gives 0 errors on 19/24 new transitions, leaving five unknown.
At 1.25 gain it gives 0/24 with full coverage. Thus the complete phase
lookup still needs gain handling; the parity gate avoids that lookup for
one linear combination of the dibit bits. The +16-bias row pairs do not
admit an exact single phase-state codebook under the same small model, yet
the gate still works on its tested streams.

This is the strongest receiver decision *candidate* so far: it is a
simple fixed Boolean readout of an executed byte, validated across changed
levels and independent streams. It is **not C3**. The OR/XOR wiring, prior
symbol storage, bit timing and route into USART-01 RxD are untraced; the
other independent dibit bit is not recovered. A bounded next test is to
look for the row-3 Y low-bit consumer or a photo-compatible latch/logic
route at the symbol boundary, then run that candidate together with a
second bit decision. Do not wait for net continuity to start that test.

The [gate report](results/receiver-mask04-row3-parity-gate.json) contains
all case scores, trace hashes, fresh seeds and source hashes. The
[gain-adaptation report](results/receiver-mask04-rowpair-gain-adaptation.json)
contains both gain-specific codebooks and holdout coverage. Reproduce with
`python3 g2/receiver_mask04_row3_parity_gate.py` and
`python3 g2/receiver_mask04_rowpair_gain_adaptation.py` from the microcode
directory.
