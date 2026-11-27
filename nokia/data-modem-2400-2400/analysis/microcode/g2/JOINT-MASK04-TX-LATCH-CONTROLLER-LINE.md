# Executed-controller A4 checks the two DAC latch routes

The fresh source-payload [line challenge](JOINT-MASK04-TX-LATCH-TOPOLOGY-LINE-CHALLENGE.md)
favored a 74LS373 hold of settled `12A` Y over a 74LS273 clock on live
`127` Y. This control uses the already executed 8031 A4 segment-2 bytes
instead of newly generated scrambler-model octets. It replays the saved
controller command and bitstream through the real PROM transmitter, checks
the full trace against the earlier [timed-latch run](JOINT-MASK04-TX-12A-DELAYED-LATCH.md),
then extracts both Y sites from each **same** trace. The controller fixture
models timer expiry and USART ready; this is not a natural wall-clock run.

Both topologies use the same sample divider, six surviving DAC bus orders,
assumed A2 mid-code mute, 1,950 Hz bandpass and +6-sample alignment. At
the already selected Q=0.5, the known-carrier decoder scores the 62
available A3/A4 phase decisions as follows:

| Controller selector | Held `12A` wrong / 62 | Live `127` wrong / 62 | Live `127` wrong decision indices |
| --- | ---: | ---: | --- |
| Call `40` | 0 on all six buses | 1 on all six buses | 42 |
| Answer `60` | 0 on all six buses | 2 on all six buses | 42, 47 |

The two interpretations differ at all 832 sampled Y bytes. Both retain a
2,100 Hz A1 tone peak, so the tone alone does not distinguish them. At
the earlier Q=1.0 control the held route still scores zero, while live
`127` scores one call and two to three answer errors depending on bus;
those counts match the saved timed-latch replay. The [machine report](results/joint-mask04-tx-latch-controller-line.json)
contains each source hash, DAC-code hash, and decision index. Reproduce with:

```sh
python3 g2/joint_mask04_tx_latch_controller_line.py
```

This independently supports the conditional held-`12A` line route with
controller-produced A4 bytes. It rejects an exact live-`127` continuation
under the fixed analog fixture, but does not identify Nokia's actual
74LS373/74LS273 clock and data nets, DAC08 pins, or line filter. C2 and
G2 remain open; continue circuit and line constraints without waiting for
continuity alone.
