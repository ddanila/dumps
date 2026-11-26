# Running R1 phase challenge of the conditional 12A line and receive path

The executed q3/mask-04 `127–12A` transmitter uses R1 as a phase
accumulator. This experiment challenges the [frozen seven-state receive
rule](JOINT-MASK04-Q05-PHASE-LEVEL-MAP.md) on the two fresh eight-byte
payloads from the [level replay](JOINT-MASK04-Q05-FRESH-PAYLOAD-LEVELS.md).
It keeps the bus-0 DAC candidate, Q=0.5 line, +6 sample alignment, and
zero-run-calibrated gain fixed.

First, seeding initial R1 with `00`, `20`, or `40` changes the full
execution digest but **does not change any sampled raw `12A` byte** in
either mode. This is not an effective line-phase challenge. The
[initial-seed report](results/joint-mask04-12a-phase-seed.json) records
that negative control; it does not identify where startup absorbs the
seed.

The running-loop test adds `20` or `40` to R1 once, immediately before
the real `127` instruction at visit 120,001, just after the 320-sample
tone/silence interval. The rest of the real-PROM run is unchanged. Both
offsets change the sampled `12A` raw-byte hash in both selectors.

| Selector | Running R1 offset | External reference errors among 64 decisions | Frozen DSC rule / modeled 8251–8031 result |
| --- | ---: | ---: | --- |
| `40` | `20` | 1, at decision 40 | Not run |
| `60` | `20` | 3, at decisions 40–42 | Not run |
| `40` | `40` | 0 | 64/64 dibits, eight line bytes, exact `D3 26 91 4E B8 07 5C EA` |
| `60` | `40` | 0 | 64/64 dibits, eight line bytes, exact `6A D5 02 B9 40 EF 73 1C` |

At offset `40`, every one of the 65 captured receive states differs
from its unperturbed counterpart, yet all 64 decoded transitions are
unchanged. The frozen rule has zero wrong and zero unknown data dibits
in both modes. With aligned assumed SYNDET, the modeled 8251 consumes
eight bytes with no overrun and the unchanged 8031 descrambles the
exact source payload. The offset-`20` errors occur at the first data
boundary; the smaller abrupt step is not robust for this fixture.

The R1 intervention is a diagnostic test, not a photographed board
command. The DAC/ADC buses, analog filter, clock/latch timing, phase
logic, serial connection and SYNDET source remain assumptions. This
result strengthens a conditional differential-phase explanation but
does not satisfy the physical C2/C3 route checks. Next test a
photo-compatible circuit for the frozen phase decision and serial
timing, and vary the instant of the phase change to separate the
boundary transient from steady-state behavior.

The [transmit report](results/joint-mask04-12a-running-phase.json) and
[receive report](results/joint-mask04-12a-running-phase-rx.json) contain
hashes, decisions, states and controller handoffs. Reproduce from the
microcode directory with:

```sh
python3 g2/joint_mask04_12a_phase_seed.py
python3 g2/joint_mask04_12a_running_phase.py
python3 g2/joint_mask04_12a_running_phase_rx.py
```
