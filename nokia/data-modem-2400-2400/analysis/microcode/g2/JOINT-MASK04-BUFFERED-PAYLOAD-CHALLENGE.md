# Buffered serial path on non-zero payloads

The [buffered zero-run handoff](JOINT-MASK04-BUFFERED-SERIAL-HANDOFF.md)
recovers an eight-zero-octet controller payload, but a single payload could
favor the frozen receive readout. This follow-up keeps the same one-symbol
serial-to-`D127` buffer, four-visit pulse, real DSC transmitter and receiver
PROMs, candidate B5/line/ADC fixture and pre-frozen 46/93 decision rule.
Only the eight offered line bytes change. These are diagnostic line streams,
not messages accepted by the 8031 protocol.

Run `python3 g2/joint_mask04_buffered_payload_challenge.py` from the
microcode directory. The [machine report](results/joint-mask04-buffered-payload-challenge.json)
records per-selector PROM cycle counts, trace digests, sample and ADC hashes,
dibits, pulse events and frozen-pair scores.

| Selector | Offered and recovered bytes | Reference errors | Frozen 46/93 errors/unknown | Adjacent dibit transitions |
| --- | --- | ---: | ---: | ---: |
| `40` | `E4 1B C7 39 55 AA 00 FF` | 0 | 0/0 of 64 checks | 14/16 |
| `60` | `93 6C 2D D2 F0 0F 81 7E` | 0 | 0/0 of 64 checks | 16/16 |

Both outputs contain all four dibits, and the frozen ADC-margin selector
also makes no errors on these two fixtures. The fixed 47/94 and 94/141
alternatives leave unknown decisions, with 94/141 also making one wrong
decision per selector. The exact 46/93 result therefore survives varied
data, not merely the zero-run payload. It does not yet establish a board
decision circuit or performance over unknown gain, timing, and noise.

The buffered bit-pair latch, `D127` pulse gate, converter buses, analog
filter, sample clocks and DSC-to-USART route remain assumed. This experiment
does not exercise the 8031 receive protocol. C2/C3 remain open; next constrain
the pulse and output routes with photo-compatible circuits and challenge the
readout at different gain and sample phase. Missing continuity is not a
reason to pause those runs.
