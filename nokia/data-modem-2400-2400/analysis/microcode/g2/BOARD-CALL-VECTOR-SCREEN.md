# One-cycle control-store call vectors after 084

The [branch-vector screen](BOARD-VECTOR-SCREEN.md) tested a hypothetical
external PROM-address takeover using direct BRT words. This [call-vector
screen](board_call_vector_screen.py) applies the same staged one-cycle handoff
to all **77** real-PROM words that decode as direct, unconditional BSR calls
under the saved sequencer rule. They encode 38 distinct targets. U9 starts at
its first `084` arrival (cycle 42); a BSR fetched from the external address
pushes internal return address `085`, then loads its encoded target. The four
PROMs, control latches, U9 and both Am2901 slices execute each case. TEST and
external D are zero, with unknown startup RAM/Q and the original q3 mapping.

Every handoff satisfies the modeled call contract: the external address is
fetched, the target becomes U9's PC, and `085` is pushed without changing the
other stack entries. The bounded 512-cycle outcomes are:

| Outcome | Calls | Meaning in this fixture |
| --- | ---: | --- |
| Return to `084` | 2 | Fetch words `01C`→`01E` and `1A2`→`300`. |
| Model stop at `089` | 75 | Each visits `085`; the POP at `089` then needs an unknown caller return address. |

Fetch `13C`→`3D5` reaches computed call site `3D7` once; fetch `13D`→`3C0`
reaches `3C2` once. No case visits `392`–`39F`, the old q3 candidate output
sites. These observations describe **one call with return address `085`**.
The 75 stops do not show that the subroutines fail in their real calling
contexts; `089` is reached because this diagnostic call supplies only one
return level. They also do not identify a Nokia external address driver or a
controller command.

The [report](results/board-call-vector-screen.json) retains each word,
target, stack check, visited PCs, stop, table-call count, output-site count,
PROM hashes and source hashes. Together with the branch-vector and
[held-input](BOARD-VECTOR-INPUT.md) screens, it narrows this particular
takeover fixture without blocking experiments on timed controller inputs,
other entry contexts or photo-compatible connections.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/board_call_vector_screen.py
```
