# Full controller zero-run through both DSC paths and the paced controller

This [joined execution](joint_mask04_full_zero_handoff.py) begins with the
unchanged 8031 scrambler's eight-byte line output for eight zero plaintext
bytes. The call and answer selectors provide different line octets. Their
64 bits become 32 D127 pulse-rule dibits after the declared 32-symbol A3
reversal preamble. Each transmitter run executes **1,257,256 real-PROM
microinstructions** and captures 838 candidate Y7 samples. The first
576 samples match the earlier real-PROM A1–A3 capture bit-for-bit; the
last six samples are now *executed* beyond A4 with D127 held at its
baseline, allowing the fixed six-sample receive alignment to retain all
32 data dibits.

The candidate B5 output, A2 mid-code gate, Q=1 analog filter and
complementary ADC route then feed a separate **768,047-instruction
real-PROM receiver run** per selector. Each accepts 24,000 ADC visits.
The independent reference receiver makes zero errors on both aligned
PCM streams. The frozen `46/93` capture pair and the previously frozen
three-pair ADC-margin selector are scored independently on the same
executed `3F8`/`3ED` bytes.

| Selector | Offered 8031 line bytes | Frozen 46/93 decisions | Margin decisions | Paced aligned 46/93 handoff |
| --- | --- | ---: | ---: | --- |
| `40` call | `62 DE 61 9D 7C 5F E5 E2` | 0 wrong, 0 unknown / 63 | 1 wrong, 0 unknown / 63 | Same eight line bytes → eight zero plaintext bytes; `AF→B0` |
| `60` answer | `A5 C2 4C 58 52 47 65 B4` | 0 wrong, 0 unknown / 63 | 0 wrong, 0 unknown / 63 | Same eight line bytes → eight zero plaintext bytes; `AF→B0` |

The first preamble dibit is a differential reference, so 63 of the 64
dibits are observable; **all 32 data dibits** are recovered by the fixed
pair. Its recovered bits serialize to the exact eight line octets above.
With the declared 416-8031-tick bit pacing, only an external SYNDET
pulse at the data boundary (bit 64) lets the narrow 8251/8031 model
consume those bytes and reach `B0`. Pulses at 63 or 65, no pulse, and
the opposite selector remain at `AF` for both call and answer.

The margin selector's call-side failure is informative. At symbol 44,
it chooses pair `94/141` because its minimum ADC distance from mid-code
is 43; that pair says dibit 3, while the true dibit is 1. The earlier
pairs `46/93` and `47/94` both say 1 despite smaller distances of 15
and 32. Thus ADC magnitude alone is not a universally safe capture
selector for this waveform. The call-side margin result is **not**
passed to the controller or silently repaired. The fixed-pair handoff
is an alternative, already frozen readout under this fixture, not an
identified Nokia decision circuit.

This is a conditional end-to-end *model* result. The D127 decoder,
Y7→74LS273 D4 connection, latch and DAC clocks, DAC08 analog path,
filter, ADC wiring, receive decision latches, RxD/RxC and SYNDET route
remain untraced. The transmitter, receiver and controller run
sequentially with modeled signal handoff, and the paced USART model is
narrow. C2 and C3 remain open. A next discriminating experiment should
test which receive phase/decision source is available on the board or
challenge the fixed 46/93 path with the same executed-Tx waveform at
other carrier phase, gain and timing offsets.

The [machine report](results/joint-mask04-full-zero-handoff.json) records
both PROM digests, sample and ADC hashes, recovered bytes, all frozen
decision scores, the margin-selector conflict and controller controls.
Reproduce from the microcode directory with
`python3 g2/joint_mask04_full_zero_handoff.py`.
