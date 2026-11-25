# A fixed phase label cannot decode the two-visit four-bit receive state

The [phase-state audit](receiver_mask04_phase_state_audit.py) reuses 987
consecutive-symbol observations from the 21 real-PROM receive traces in the
[two-visit transition study](RECEIVER-MASK04-TWO-VISIT-TRANSITIONS.md).
It checks a specific small consumer hypothesis: assign each four-bit
`3F8` Y6/Y7 state a fixed quadrature phase `P[state]`, then obtain the
dibit from a constant phase advance plus `P[current] - P[previous]`.
The phase steps are the reference modem's `00→0`, `01→1`, `10→3`,
`11→2` quadrants. No physical phase-label circuit is claimed.

The 86 observed transition keys remain individually unambiguous. But
**696 transitions keep exactly the same four-bit state while the known
dibit is `11`**, a 180° reversal. Any fixed-label model must therefore
add a constant two-quadrant step. Three other executed transition keys
then make that impossible:

| State transition | Known dibit | Required change in `P` after subtracting the 180° step | Source |
| --- | ---: | ---: | --- |
| `0→4` | `11` | 0 | 90° grid, symbol 2 |
| `4→8` | `11` | 0 | 45° grid, symbol 34 |
| `8→0` | `01` | 3 | 150° intermediate, symbol 35 |

The states return to 0, so the changes in `P` must sum to zero modulo four;
these sum to three. This is an exact counterexample to **any** fixed phase
label for the 16 four-bit states and **any** constant baseline advance.
It is not a failure of the executed receive loop or proof that a direct
transition circuit cannot work. The earlier 86-key direct lookup still has
zero conflicting observed labels and five unknown decisions on the third
stream. The [machine report](results/receiver-mask04-phase-state-audit.json)
records the source trace digests, self-transition counts and cycle witnesses.

The next C3 experiment should test a direct pair-to-dibit decision or
additional retained/timing state against fresh angles and streams, then
serialize the surviving decisions toward a photo-compatible 8251A RxD/RxC
route. The ADC wiring, both capture instants and USART connection remain
explicit assumptions; C3 stays open. Reproduce from the microcode directory
with `python3 g2/receiver_mask04_phase_state_audit.py`.
