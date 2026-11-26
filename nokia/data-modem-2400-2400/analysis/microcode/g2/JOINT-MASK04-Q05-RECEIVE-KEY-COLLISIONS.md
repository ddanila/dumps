# An alternate two-visit capture avoids the improved line's key collisions

The [first Q=0.5 receiver replay](JOINT-MASK04-12A-Q05-RECEIVER.md)
left many nonzero data dibits unknown. This
[audit](joint_mask04_q05_receive_key_collisions.py) replays the same
first eight-byte payload in both controller selector modes and matches
the saved transmitter, PCM, ADC and receiver trace hashes. For each
of the 64 data decisions it compares four-bit transitions from the
executed `3F8` Y capture at visits 46/93, 47/94 and 94/141. The
primary feature uses Y6/Y7 at both visits; the alternative uses
Y5–Y7 at the first and Y7 at the second.

| Visit pair and feature | Distinct keys | Keys with different observed dibits | Positions on conflicting keys |
| --- | ---: | ---: | ---: |
| 46/93 primary | 9 | 5 | 50 |
| **46/93 alternative** | **16** | **0** | **0** |
| 47/94 primary | 19 | 3 | 24 |
| 47/94 alternative | 15 | 3 | 21 |
| 94/141 primary | 35 | 1 | 3 |
| 94/141 alternative | 32 | 1 | 3 |

The conflict-free 46/93 alternative reaches exactly four symbol states:
`5`, `8`, `C`, `D`. All sixteen transitions occur. The observed labels
are consistent with assigning successive phase quadrants 0, 1, 2, 3
to those states and subtracting the 180° carrier advance per symbol.
That is a small differential phase hypothesis rather than a table of
unrelated exceptions. The other tested four-bit features have actual
collisions on this fixture and cannot uniquely decide every observed
data dibit by their key alone.

This screen uses the same two streams to inspect labels and choose the
four-state rule. It is discovery data, not a held-out C3 result. The
[frozen follow-up](JOINT-MASK04-Q05-PHASE-STATE-HOLDOUT.md) tests the
second payloads. The capture clock, ADC path, external phase logic and
USART wiring remain photo-compatible assumptions.

The [machine report](results/joint-mask04-q05-receive-key-collisions.json)
contains every key, label and collision witness. Reproduce with
`python3 g2/joint_mask04_q05_receive_key_collisions.py` from the
microcode directory.
