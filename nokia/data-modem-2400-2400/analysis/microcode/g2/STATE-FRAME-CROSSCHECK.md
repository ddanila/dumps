# Controller state and outgoing frame cross-check

This joins two independently saved executions of the unchanged 8031 ROM:
[state-matrix](results/state-matrix.json) starts at `1000` with an imposed
countdown reload or expiry, while [controller-frames](results/controller-frames.json)
starts at `1EE2` and sends all four bytes under one fixed flag/payload fixture.
The runs do **not** preserve a single CPU/RAM image between these entry points,
so each row is a pair of conditional observations, not a complete call trace.

| RAM34 state | Reloaded ticks | Expiry successor | Four transmitted bytes |
| --- | ---: | --- | --- |
| A0 | 1805 | A1 | `80 02 88 7A` |
| A1 | 2605 | A2 | `80 02 81 7A` |
| A2 | 60 | B8 | `80 02 88 7A` |
| A3 | 23 | A4 | `D0 42 81 BA` |
| B8 | 70 | B4 | `D0 42 81 22` |
| A6 | 2000 | A3 | `D0 42 89 3A` |
| A7 | 250 | A8 | `D0 42 88 7A` |
| AA | 580 | AB | `D0 42 81 EA` |
| AB | 25 | AC | `D0 42 88 EA` |

A0 and A2 have distinct countdowns and expiry successors, yet emit the exact
same four-byte frame in this fixture. Therefore the frame cannot uniquely
encode the controller's RAM34 state. A1 changes only the third byte relative
to A0/A2 (`88` to `81`). These byte changes are observations, not identified
tone, training or data commands. In particular, the similar timing of these
states to V.26 ter operating windows does not establish which signal each
state requests.
The [P1 channel replay](CONTROLLER-STATE-PIN-CHANNELS.md) adds a separate
observed signal: A0 leaves P1.5 high, while A1 and A2 leave it low. Thus the
controller can distinguish A0 from A2 even though their serial frames match;
the destination and meaning of this pin are still unknown.

The separate [receive-to-state experiment](results/receive-state.json) also
shows that received payload and flags can affect both the next state and
outgoing bytes. A controller-to-DSP emulator must therefore carry those
variables through a continuous call before assigning a command meaning to a
frame. The physical recipient of the frame still needs to be traced.

## Preserved-RAM chain

The [chain probe](chain_frames.py) now keeps one 8031 RAM/SFR image across
four successive state steps and four actual sends. It starts at A0 and
directly sets RAM2E to each of 256 possible values. The harness forces timer
expiry and directs PC to the state and send entry points at each step; these
handoffs are not a natural uninterrupted call. All 256 executions finish
without emulator errors and form exactly four state/frame chains:

| RAM2E bits 6,0 | State chain after each expiry | Frames after A0, A1, A2, fourth step |
| --- | --- | --- |
| 0,0 | A1 → A2 → B8 → B4 | `80 02 81 7A`; `80 02 88 7A`; `D0 42 81 22`; `D0 42 81 EA` |
| 0,1 | A1 → A2 → B8 → B4 | same first two; `C0 42 81 22`; `C0 42 81 EA` |
| 1,0 | A1 → A2 → A3 → A4 | same first two; `D0 42 81 BA`; `D0 42 81 BA` |
| 1,1 | A1 → A2 → A3 → A4 | same first two; `C0 42 81 BA`; `C0 42 81 BA` |

This is stronger than combining separate fixed fixtures: the output routine
can modify RAM before the next state step. It shows that the branch and frame
differences survive that interaction. It still does not identify the physical
DSP command semantics, since RAM2E is directly injected and the timer and PC
handoffs are synthetic. The [full report](results/chain-frames.json) retains all 256 chains
and source hashes.
