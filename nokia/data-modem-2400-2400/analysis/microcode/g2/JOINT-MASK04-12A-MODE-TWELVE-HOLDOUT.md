# Fresh changed-mode payloads at a new carrier phase

The earlier [mode-conditioned phase gate](JOINT-MASK04-12A-MODE-PHASE-HOLDOUT.md)
passed its answer-side mode-condition holdout at R1 offset 112. We froze
that eight-state gate and challenged it with two **new controller payloads**
at offset 120, keeping the Q=0.5 line, +5 sample shift, 100% line level
and the assumed `81→A1` `3EB` mode edge at
read 48,001. Both real-PROM Tx→line→Rx runs sustained the four-row path;
the independent reference decoder made 0/64 errors in each. The gate
failed: **9/64 call** and **12/64 answer** decisions, so neither line nor
controller bytes recovered. The [failed challenge](results/joint-mask04-12a-mode-fresh-phase120.json)
is retained as a negative result.

Both streams introduced the same four captured states: `19`, `2D`, `36`
and `59`. A combined phase graph has zero conflicts and fixes the phase
of `36` at 0 after anchoring the eight earlier states. The frozen gate
assigned `36` phase 1; every wrong decision touched that state. Its
other three unseen-state predictions agreed with the graph. This is a
specific Boolean extrapolation failure, not evidence that the PROM
receiver stopped or the phase graph became inconsistent.

The [12-state revision](joint_mask04_12a_mode_phase_twelve.py) moved that
failed pair into development, froze new two-output Boolean covers, and
then tested a **separate new payload pair** at the same offset and mode
schedule. No gate term, line setting or timing was changed after those
holdout payloads were chosen.

| Fresh 12-state holdout | Reference errors | Frozen gate errors | Line bytes | Executed 8031 source bytes |
| --- | ---: | ---: | --- | --- |
| Call `40` | 0/64 | **0/64** | Exact eight | Exact eight |
| Answer `60` | 2/64 | **0/64** | Exact eight | Exact eight |

The [holdout audit](joint_mask04_12a_mode_twelve_audit.py) checks all 12
trained phase labels against the combined development/holdout transition
graph, which has zero conflicts, and verifies exact modeled 8251/executed
8031 bytes with no controller errors or overruns. The answer-side reference
misses two dibits on this fixed fixture while the executed-PROM candidate
readout remains exact; the independent decoder and candidate gate are
different algorithms. No new state appears in this holdout, so the result
establishes transfer to new data under this observed state alphabet, not
arbitrary carrier phase or gain.

The [revised model](results/joint-mask04-12a-mode-phase-twelve.json),
[holdout](results/joint-mask04-12a-mode-twelve-holdout.json) and
[audit](results/joint-mask04-12a-mode-twelve-audit.json) preserve all
source hashes, capture states, wrong indices and decoded bytes. Reproduce
from the microcode directory with:

```sh
python3 g2/joint_mask04_12a_mode_fresh_phase120.py
python3 g2/joint_mask04_12a_mode_phase_twelve.py
python3 g2/joint_mask04_12a_mode_twelve_holdout.py
python3 g2/joint_mask04_12a_mode_twelve_audit.py
```

C3 and G2 remain open and active. The mode byte route, seven-bit capture,
Boolean consumer, RxD/RxC and SYNDET are still photo-compatible circuit
assumptions. Next freeze this 12-state gate at a further carrier phase or
line level and test the assumed mode-bit selector and physical serial
route; do not promote a fitted external readout to an executed DSC bit
decision.
