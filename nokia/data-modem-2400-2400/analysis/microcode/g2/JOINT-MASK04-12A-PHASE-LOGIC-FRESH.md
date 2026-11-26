# Fresh carrier starts reject the static six-bit phase decoder

The [phase-logic model](JOINT-MASK04-12A-PHASE-LOGIC.md) assigned one
of four phases to each observed six-bit `3F8` Y state and decoded a
dibit from consecutive phase differences. Its Boolean circuit and
dibit convention were frozen before this challenge. I offered new
eight-byte source payloads in both selector modes, used the existing
mode-specific scrambler recurrence, and ran the real q3/mask-04 PROM
transmitter and receiver at one-time R1 offsets **16** and **80**.
The DAC bus, Q=0.5 line filter, nominal zero-run gain and 46/93 receive
capture visits match the earlier holdouts.

| R1 offset | Selector | New source bytes | Frozen 91-key lookup unknown | Frozen Boolean phase errors | Independent reference errors |
| ---: | --- | --- | ---: | ---: | ---: |
| 16 | `40` | `53 A1 0C F7 2D 84 B9 6E` | 63/64 | 19/64 | 0/64 |
| 16 | `60` | `C4 37 9A 05 E2 71 8F D0` | 62/64 | 24/64 | 0/64 |
| 80 | `40` | `53 A1 0C F7 2D 84 B9 6E` | 29/64 | 20/64 | 0/64 |
| 80 | `60` | `C4 37 9A 05 E2 71 8F D0` | 31/64 | 19/64 | 0/64 |

Every stream contains all four dibit values. Both new six-bit states
`01` and `35` appear in each run, but the failure is not limited to
them: respectively 5, 3, 2 and 6 wrong decisions occur on transitions
whose *two* states were already known in development. No run recovers
the full eight line bytes or reaches an exact modeled 8251/8031
handoff through this Boolean rule.

Adding each fresh offset to the 14 development cases leaves **no**
consistent phase assignment under any of the 24 dibit-to-quarter-turn
conventions. The best assignments have 52 conflicts at offset 16 and
40 at offset 80 (92 combined). Thus a static phase attached to this
six-bit two-capture state cannot explain the expanded traces, even if
the two new states are assigned new phases. The earlier exact offset
32/96 results were real but too narrow to establish this decoder.
The reference receiver's exact decisions show that the candidate line
itself still carries the data under these fixtures.

The [offset-16 report](results/joint-mask04-12a-phase-logic-fresh-16.json),
[offset-80 report](results/joint-mask04-12a-phase-logic-fresh-80.json)
and [graph audit](results/joint-mask04-12a-phase-logic-fresh-audit.json)
record the real-PROM traces, full Y samples, decisions, unknown keys,
known-state errors, controller readout and source hashes. Reproduce with:

```sh
python3 g2/joint_mask04_12a_phase_logic_fresh.py
python3 g2/joint_mask04_12a_phase_logic_fresh_audit.py
```

This rejects the **static six-bit phase rule**, not DPSK demodulation
by the microprogram. The receiver may need carrier/timing history,
another Y visit, or a different photo-compatible latch route. Keep
C3/G2 open and use these failed cases as development data only after
choosing the next candidate; reserve new payloads and carrier starts
for its untouched validation. No new photograph is required to run
that test.
