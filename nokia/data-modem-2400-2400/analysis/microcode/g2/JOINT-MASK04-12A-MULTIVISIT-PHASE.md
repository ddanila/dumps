# Multi-visit receive captures narrow a row-output phase hypothesis

The static six-bit two-Y rule failed across carrier starts and gain.
I reran its offset-16/80 failures, its offset-32/96 nominal successes,
and the two 75%-gain call/answer witnesses with full real-PROM receive
snapshots at symbol-relative visits 46, 47, 93, 94 and 141. Each replay
was checked against its prior Tx/Rx digests, ADC hash and original Y
captures before using the new `3ED` row values. This supplies 12 cases,
780 symbol snapshots and 768 labelled receive transitions.

The six-bit baseline has 40 four-phase graph conflicts on this set.
Screening all eight bits of `3F8` Y, `3ED` row 0 and `3ED` row 3 at all
five visits (120 candidates) finds 42 zero-conflict single-bit
extensions. **No bit at visit 141** removes the conflicts; its best
still has 28. One specific near-sample candidate, `3ED` row-0 bit 0
at visit 46, gives a single connected 11-state phase graph with no
conflicts under either mirror-image DPSK convention. Its bit stream
differs from first-Y4 on 631/780 symbols and second-Y5 on 679/780,
so it is a distinct executed signal rather than a copy of the prior
Y-bit choices. This candidate was selected from labelled development
data; the screen does not establish a latch or a Nokia output pin.

I froze that row-0 bit, its 11-state phase map and dibit convention,
then ran a new eight-byte source payload in each selector mode at R1
offsets 0 and 64, with real-PROM Tx→line→Rx and nominal gain:

| Offset | Selector | Frozen row-0 wrong / unknown among 64 decisions | New states | Six-bit lookup / independent reference errors |
| ---: | --- | ---: | --- | ---: |
| 0 | `40` | 0 / 63 | `08 0C 55` | 0 / 0 |
| 0 | `60` | 0 / 62 | `08 0C 55` | 0 / 0 |
| 64 | `40` | 0 / 30 | `08 0C 55` | 0 / 0 |
| 64 | `60` | 0 / 28 | `08 0C 55` | 0 / 0 |

The row-0 decoder cannot recover complete line bytes or drive the
modeled 8251/8031 payload handoff on any of these frozen cases. Adding
their labels **after the fact** preserves a zero-conflict, connected
four-phase graph and grows it from 11 to 14 states. That shows the
candidate can be extended, but it is not a passed holdout or a rule
for predicting an unseen state's phase. The old six-bit lookup happens
to work on these offsets but had failed at 16 and 80; neither narrow
success establishes the physical receiver.

The [five-visit screen](results/joint-mask04-12a-multivisit-phase-screen.json)
and fresh [offset-0](results/joint-mask04-12a-row0-fresh-0.json) and
[offset-64](results/joint-mask04-12a-row0-fresh-64.json) reports, plus
the [post-hoc graph audit](results/joint-mask04-12a-row0-fresh-audit.json),
record the full snapshots, phase states, decisions, trace hashes and
modeled readout. The supporting capture reports are
[offset 16](results/joint-mask04-12a-third-capture-16.json),
[offset 80](results/joint-mask04-12a-third-capture-80.json),
[offset 32](results/joint-mask04-12a-third-capture-baseline-32.json),
[offset 96](results/joint-mask04-12a-third-capture-baseline-96.json)
and [low gain](results/joint-mask04-12a-third-capture-low-gain.json).
Reproduce from the microcode directory with:

```sh
python3 g2/joint_mask04_12a_third_capture.py
python3 g2/joint_mask04_12a_third_capture_baseline.py
python3 g2/joint_mask04_12a_third_capture_low_gain.py
python3 g2/joint_mask04_12a_multivisit_phase_screen.py
python3 g2/joint_mask04_12a_row0_fresh.py
python3 g2/joint_mask04_12a_row0_fresh_audit.py
```

The photographed ADC and nearby latches make an external capture path
plausible, but the `3ED` row-0 bit is currently an internal emulated
signal. No observed board net shows it clocked into a phase or USART
circuit. C3/G2 remain open. The next useful test should constrain a
carrier/timing state or latch edge that predicts new phase states
without learning them from payload labels, and then use new payloads
and starts for validation.
