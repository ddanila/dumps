# Buffered receive readout depends on sample alignment

The [non-zero buffered streams](JOINT-MASK04-BUFFERED-PAYLOAD-CHALLENGE.md)
were exact at a six-sample offset after the assumed line filter. This
follow-up moves only the analog/ADC selection point one 9,600-sample/s tick
earlier or later. It holds each stream's nominal gain fixed and reconstructs
the Y7 source from the verified phase recurrence, requiring the first 846
bits and nominal PCM to hash-match the saved real-PROM transmitter run. The
one extra tail sample for the late case is projected from the same declared
`D127` input. Each shifted PCM stream then runs through 780,047 real-PROM
receiver instructions and the previously frozen decision rules.

| Selector | Sample offset | Reference wrong | Frozen 46/93 wrong / unknown data dibits | ADC-margin wrong / unknown data dibits |
| --- | ---: | ---: | ---: | ---: |
| `40` call | 5 | 2 | 0 / 0 | 0 / 0 |
| `40` call | 7 | 0 | 0 / 4 | 0 / 0 |
| `60` answer | 5 | 1 | 0 / 0 | 0 / 0 |
| `60` answer | 7 | 0 | 0 / 3 | 0 / 0 |

The independent reference decoder's early-offset errors are at symbols
34/52 for call and 35 for answer. The late fixed-readout abstentions are at
38/46/54/56 and 39/45/61 respectively. None is silently filled with an
expected dibit. The margin selector resolves all late abstentions in these
two streams, but it made one error on the nominal buffered call zero-run;
this is a fixture-specific improvement, not a general decoder claim.

The real board's DAC/ADC clock phase, filtering, sample hold, decision
logic and USART connection remain untraced. This test narrows the timing
tolerance of the candidate readout, not C3's physical acceptance evidence.
Keep C3 open; test a photo-compatible sample/decision circuit and additional
gain and phase cases while G2 remains active.

Run `python3 g2/joint_mask04_buffered_sample_phase.py` from the microcode
directory. The [machine report](results/joint-mask04-buffered-sample-phase.json)
contains PCM/ADC hashes, receiver trace digests, frozen-pair scores and
the selected margin pair for each symbol.
