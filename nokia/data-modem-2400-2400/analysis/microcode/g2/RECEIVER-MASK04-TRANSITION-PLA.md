# Direct Boolean transition logic fits observed dibits but misses new keys

The [transition-logic screen](receiver_mask04_transition_pla.py) tests a
direct consumer for the two-visit four-bit state after the
[fixed-phase-state audit](RECEIVER-MASK04-PHASE-STATE-AUDIT.md) excluded a
per-state phase table. Its input is the previous state and current state,
eight bits total. It treats the 86 observed transition keys as a partial
truth table, enumerates Boolean product terms that contradict no observed
output, and uses one fixed greedy rule to cover each of the two dibit bits.
The other 170 input keys are don't-cares during fitting. This is a candidate
external logic circuit, not a microinstruction or photographed connection.

| Check | Result |
| --- | ---: |
| Final circuit | 17 product terms, 59 input literals |
| Development keys | 0/86 wrong |
| Leave one carrier angle out | 20/987 wrong; all 20 among 58 unseen keys |
| Third-seed fresh stream, 13 angles | 2/611 wrong |

The fresh errors are both data decisions at 135°: transition `E8` was
predicted `11` instead of `01`, and `7B` was predicted `01` instead of
`11`. Both were among the five unknown keys in the earlier frozen lookup.
The other three unknown keys were predicted correctly, but those successes
do not establish a physical decoder. The angle holdouts show the same
generalization problem more clearly: a circuit that exactly covers known
keys can still choose wrong outputs for new carrier phases.

The [machine report](results/receiver-mask04-transition-pla.json) contains
all term masks and values, holdout scores and fresh error locations. This
rejects **this fitted combinational rule** as a complete C3 readout. It does
not rule out every direct logic network; a circuit may need more executed
bits, retained state or a different capture phase. The two capture clocks,
pair memory, serializer and USART-01 RxD/RxC route remain untraced hypotheses.
Keep C3 open and test a richer consumer on fresh streams rather than filling
the two errors from their known answers. Reproduce from the microcode
directory with `python3 g2/receiver_mask04_transition_pla.py`.
