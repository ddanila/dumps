# Two-bit receive phase holdouts

The [one-bit holdout](JOINT-MASK04-12A-ROW1-PHASE-HOLDOUT.md) showed that
row-0 Y1 at visit `46` alone does not transfer to carrier `143`. A
22-stream development graph selected one further capture, `3F8` Y4 at
visit `94`. The resulting nine-bit state contains the earlier seven
captured bits, row-0 Y1, and later Y4. Its 31-code phase table was frozen
before four new real-PROM/controller streams at carrier starts `145` and
`147`, with new payloads and 0.75× receive gain.

| Carrier | Selector | New key | Wrong transitions between known keys | Modeled clipping |
| --- | --- | --- | ---: | ---: |
| `145` | `40` | `1DB` | 0 | 0 |
| `145` | `60` | `1DB` | 0 | 0 |
| `147` | `40` | `1CC` | 0 | 0 |
| `147` | `60` | `1CC` | 0 | 0 |

The frozen 31-code table cannot classify a full stream containing an
unseen key, so these are coverage failures, not controller passes.
Joining the four streams with the 22 development streams makes a single
33-code phase graph with zero conflicts and constrains `1DB` to relative
phase 3 and `1CC` to 2. With those labels added, all four **development
replays** recover 64/64 dibits, exact modeled line bytes, and exact bytes
from the executed 8031 controller. This replay uses data that supplied
the new labels and therefore is not independent validation.

The 33-code table was then frozen for four untouched streams at carrier
starts `149` and `151`, again at 0.75× gain:

| Carrier | Selector | Unseen keys | Dibit errors | Line bytes | Executed controller bytes | Clipped samples |
| --- | --- | ---: | ---: | --- | --- | ---: |
| `149` | `40` | 0 | 0/64 | Exact | Exact | 0 |
| `149` | `60` | 0 | 0/64 | Exact | Exact | 0 |
| `151` | `40` | 0 | 0/64 | Exact | Exact | 0 |
| `151` | `60` | 0 | 0/64 | Exact | Exact | 0 |

The modeled capture is ready 2,929 microcycles before the first RxC edge.
The earlier [U14/U12/U3 storage schedule](JOINT-MASK04-12A-VISIT94-LATCH-ROUTE.md)
has capacity for this state if U12 retains first Y6 plus row-0 Y0/Y1 and
U14's reused pair captures later Y4 rather than later Y6. That schedule
is a package-capacity hypothesis; the actual data/enable nets and phase
gate have not been identified. The line/ADC and DSC-to-USART connections
also remain assumed. The tests establish transfer of a **lookup under
those assumptions** across these new carriers and payloads, not the
physical Nokia receiver circuit or a C3 acceptance pass.

The scripts and source-hashed reports are:

- `joint_mask04_12a_two_bit_phase_holdout.py` and
  `results/joint-mask04-12a-two-bit-phase-holdout.json` for the frozen
  31-code challenge;
- `joint_mask04_12a_two_bit_phase_extension.py` and
  `results/joint-mask04-12a-two-bit-phase-extension.json` for the
  33-code development graph and replay;
- `joint_mask04_12a_two_bit_phase_frozen33.py` and
  `results/joint-mask04-12a-two-bit-phase-frozen33.json` for the fresh
  33-code holdout. Their per-carrier reports retain the full captures.

Next test a different gain family and construct a gate/latch route within
the photographed package budget. Keep C3 and G2 active while those
connections are hypotheses.
