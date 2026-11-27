# Fresh line-score challenge of the two DAC latch topologies

The [B5 topology comparison](JOINT-MASK04-TX-LATCH-B5-DISCRIMINATOR.md)
found that a 74LS373 hold of settled `12A` Y and a 74LS273 clock on live
`127` Y predict different DAC08 B5 input values on most sample clocks. To
test the line consequence without relying on a new pin measurement, this
challenge runs two previously unused eight-byte source payloads through
the established line-side scrambler model and real PROM transmitter, one call
and one answer. These new bytes are not a separate executed 8031 trace.
Each run collects both
Y sites from the **same executed trace** and applies the same 375-visit
sample divider, six surviving DAC bit orders, Q=0.5 candidate line filter,
+6-sample alignment and gain calibrated earlier on a separate zero-run.
The gain and filter were not fitted to these payloads or to either latch
topology in this challenge.

| Selector | Different held-`12A` vs live-`127` samples | Held `12A`: wrong / 64 dibits | Live `127`: wrong / 64 dibits |
| --- | ---: | ---: | ---: |
| Call `40` | 852/852 | 0 on all six buses | 5 on all six buses |
| Answer `60` | 852/852 | 0 on all six buses | 1 on all six buses |

The same decision counts hold at 0.75×, 1.0× and 1.25× fixed gain. There
is no clipping at nominal gain. The call live-`127` errors are at symbols
39, 40, 43, 44 and 50; the answer error is at symbol 61. These are data
symbols. Thus the held-`12A` interpretation predicts the intended DPSK line
stream more consistently under this frozen analog fixture. This rejects
the specific shared-live-`127` continuation as an **exact** line model on
these fresh inputs; it does not identify the physical latch wiring or rule
out other analog stages.

The [machine report](results/joint-mask04-tx-latch-topology-line-challenge.json)
contains each PCM hash, error index, gain and source hash. Reproduce with:

```sh
python3 g2/joint_mask04_tx_latch_topology_line_challenge.py
```

C2 remains open because the 74LS373/74LS273 data and clock nets, DAC08
pins and analog output are not independently established. The known-carrier
decoder is external to the DSC. Continue with a photo-compatible pin/clock
constraint or a new circuit control; do not pause G2 for continuity alone.
