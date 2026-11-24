# Candidate controller bytes after a one-cycle vector to 133

The [one-cycle vector screen](BOARD-VECTOR-SCREEN.md) found that fetching the
real-PROM BRT at `111` reaches computed call sites `3D7` and `3C2` before
returning to the `084` wait loop. This [input screen](board_vector_input.py)
repeats that hypothetical handoff, then holds one candidate external D byte
and TEST level through the path. Eight byte values occur in actual 8031
four-byte output frames; `00` and `FF` are controls. The bytes are **not**
asserted to reach the DSC 2847 as a parallel bus, and holding one byte is a
diagnostic timing assumption, not a replay of the serial frame.

The initial reset prefix uses TEST=0 and D=0 and reaches `084` at cycle 42.
For each of the ten D values and both TEST levels, the four-PROM board model
runs from three RAM/Q startup assumptions: unknown (the model default), all
zero, and all one. The two seeded states are explicit counterfactuals that
expose sensitivity otherwise hidden by unknown bits.

| Startup RAM/Q | TEST | Distinct control-flow traces across ten D bytes | Distinct final Am2901 states | Computed calls | Return to `084` |
| --- | ---: | ---: | ---: | --- | --- |
| Unknown | 0 | 1 | 1, all 136 RAM/Q bits unknown | `3D7` and `3C2`, once each | 41 cycles |
| Unknown | 1 | 1 | 1, all 136 RAM/Q bits unknown | None | 21 cycles |
| Zero | 0 | 1 | 10 | `3D7` and `3C2`, once each | 41 cycles |
| Zero | 1 | 1 | 10 | None | 21 cycles |
| All one | 0 | 1 | 10 | `3D7` and `3C2`, once each | 41 cycles |
| All one | 1 | 1 | 10 | None | 21 cycles |

In the seeded cases, the final RAM/Q fingerprint differs for every D byte;
the candidate D input therefore affects arithmetic state under this q3
mapping. TEST changes the path but the held D byte does not change its
microaddress sequence. All 60 runs return to `084` and none visits `392`–`39F`,
the old q3 candidate output sites. The Y value at both computed call words is
`00` in the TEST=0 cases. This is evidence of input sensitivity in a short
branch path, not a command-dependent DAC stream or a decoded modem routine.

The [machine-readable report](results/board-vector-input.json) includes each
case's exact stimulus, control-flow digest, table-call count, final RAM/Q
fingerprint, PROM hashes and source hashes. The next useful experiment needs a
plausible **timed** controller-to-DSP route or another photo-compatible field
mapping; neither the unknown physical net nor this short path blocks G2.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/board_vector_input.py
```
