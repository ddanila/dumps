# One controller TxD bit changes the executed Y7 carrier one symbol later

The [buffered serial handoff](JOINT-MASK04-BUFFERED-SERIAL-HANDOFF.md)
uses a labelled one-symbol pair buffer between the 8031/8251's actual
2,400-bit/s TxD stream and the DSC's D127 input. The
[bit-ablation replay](joint_mask04_buffered_txd_bit_ablation.py) checks
that buffer against the executed transmitter, rather than treating
its dibits as already available at symbol start.

First, the R1 recurrence independently reconstructs the **846 sampled
Y7 bits** and exact SHA-256 hashes saved from four full real-PROM
buffered streams: zero-run and nonzero payloads in both selectors.
The recurrence starts at the previously checked R1 phase and adds each
scheduled D127 byte modulo 256; its predicted high bit matches the
saved executed output at every sample.

Next, for each selector, the replay flips **TxD bit 40** of the actual
controller zero-run line-byte stream from 1 to 0. This is a controlled
counterfactual, not a claim that the controller emitted the altered byte.
The paired buffer stores that bit, sees the pair's second bit at visit
61,500 of the data fixture, and emits the complete pair's pulse at
visit 63,000, the following symbol boundary. Including the earlier
A1–A3 prefix, only four D127 visits, **279,000–279,003**, change
from `90` to `80`. The R1 recurrence predicts `4×(80−90) ≡ 192`
modulo 256: a −90° carrier-phase step.

| Selector | Mutant PROM words | First changed Y7 sample / 846 | Changed Y7 samples | Mutant Y7 vs independent recurrence |
| --- | ---: | ---: | ---: | --- |
| Call `40` | 1,269,256 | **744** | 51 | 846/846 exact |
| Answer `60` | 1,269,256 | **744** | 51 | 846/846 exact |

Both mutant runs keep the complete transmitter loop and change its
PROM trace digest. No sampled Y7 bit changes before the altered pulse;
the first change is at the predicted sample boundary. The same
quarter-turn model accounts for both distinct controller streams.
Together with the direct [full-A4 R1/Y7 check](JOINT-MASK04-TX-PHASE-PULSE-ABLATION.md),
this connects one real controller TxD bit, a causal buffered-pair
hypothesis and the executed carrier bit in a falsifiable chain.

The paired-bit latch, symbol clock, D127 mask gate, 9,600-Hz output
clock, Y7-to-DAC08 data route and line current remain untraced
assumptions. The replay identifies digital behavior under that circuit;
it does not pass C2 or prove Nokia built the buffer exactly this way.
The [machine report](results/joint-mask04-buffered-txd-bit-ablation.json)
contains all four saved-stream hash controls, the two mutant PROM
digests, changed input visits, output sample counts and source hashes.
Reproduce from the microcode directory:

```sh
python3 g2/joint_mask04_buffered_txd_bit_ablation.py
```
