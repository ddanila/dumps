# Non-zero payload holdout for the full-byte joined path

The [full-byte DAC/receiver handoff](JOINT-MASK04-BUFFERED-FULL-BUS-LOOPBACK.md)
proposed a fixed-first receive rule after seeing a zero-run fixture:
take the frozen `46/93` decision when known, otherwise use the separately
frozen ADC-margin selector. This holdout applies that **unchanged rule**
to two non-zero eight-byte streams. Those bytes were recorded earlier in
the [one-bit-DAC challenge](JOINT-MASK04-BUFFERED-PAYLOAD-CHALLENGE.md),
before the full-byte fallback was proposed. The DAC bus order
`[4,0,6,1,3,2,5,7]`, candidate latch words `127`/`129`, line filter,
ADC schedule and PROM receive tables are also unchanged.

Each selector executes 1,269,256 real DSC transmit instructions; the
`127` Y7 stream hash must match its earlier saved one-bit run. Each of
the four full-byte analog/ADC cases then executes 780,047 real DSC
receive instructions. The independent reference decoder has zero errors
on all four candidate waveforms.

| Selector | Latch words | Offered and recovered line bytes | Frozen 46/93 wrong/unknown data dibits | Margin wrong/unknown | Fixed-first wrong/unknown |
| --- | --- | --- | ---: | ---: | ---: |
| `40` call | `127`, `129` | `E4 1B C7 39 55 AA 00 FF` | 0/2 | 0/0 | 0/0 |
| `60` answer | `127`, `129` | `93 6C 2D D2 F0 0F 81 7E` | 0/9 | 1/0 | 0/0 |

The answer margin error is at symbol 42, where the fixed 46/93 decision
is known, so the fallback preserves that decision. It fills only fixed
abstentions and recovers all 32 data dibits and exact eight bytes in each
held-out case. The answer stream contains all four dibits and all 16
adjacent-dibit transitions. This supports the conditional full-byte
modulation and PROM receive dataflow beyond the zero-run payload. It
does not prove analog or decision performance over untested gain, clock
phase and noise.

The DAC input order, latch clock, A2 gate, line filter, complementary ADC,
onboard decision gates and USART path remain labelled hypotheses. These
arbitrary line bytes are not an 8031 zero-run protocol handoff. C2/C3
stay open; constrain those physical routes and challenge the frozen
readout on new signal levels and timings without treating absent
continuity as a blocker.

Run `python3 g2/joint_mask04_full_bus_payload_holdout.py` from the
microcode directory. The [machine report](results/joint-mask04-full-bus-payload-holdout.json)
records all four PROM trace digests, sample hashes, frozen decision
scores and recovered byte streams.
