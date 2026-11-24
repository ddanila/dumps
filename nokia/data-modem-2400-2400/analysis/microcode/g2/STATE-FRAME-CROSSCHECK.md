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

The separate [receive-to-state experiment](results/receive-state.json) also
shows that received payload and flags can affect both the next state and
outgoing bytes. A controller-to-DSP emulator must therefore carry those
variables through a continuous call before assigning a command meaning to a
frame. The physical recipient of the frame still needs to be traced.
