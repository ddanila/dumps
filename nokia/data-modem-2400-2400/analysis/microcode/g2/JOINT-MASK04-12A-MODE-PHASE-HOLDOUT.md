# Receive phase readout across an assumed controller mode edge

The [full-PROM mode run](joint_mask04_12a_row_mode_edge.py) holds `81` or
offers `81→A1` at the assumed `3EB` external D input during the call-side
phase-112 controller-fed line. The edge is placed at read 48,001, around
the 32-symbol preamble/data boundary. Both runs sustain the same executed
PC sequence and the [two-edge row clock](JOINT-MASK04-12A-ROW-CLOCK-TWO-EDGE.md):
97,500 `3ED→3EA` row captures and 97,501 `3EA→3EB` counter edges.
The mode edge changes the saved capture values in all 33 symbols from
symbol 32 onward, without changing the PC path. This is a direct-`3EB`
**wiring hypothesis**, not a measured controller-to-DSC net.

The former 22-state phase gates were fitted under the assumed `01` mode
input. On the call-side held-`81` and edge streams, they make 21 and 13
wrong decisions, respectively. The changed seven-bit states form a
conflict-free four-phase graph with the old call-side `01` stream. We
anchored its old states to their frozen phase labels, fitted two Boolean
outputs on the eight observed call states, and **froze** those gates before
running the answer-side payload under the same two mode scenarios.
That payload was part of the earlier `01`-mode gate development; the
held-`81` and `81→A1` executions and their capture states were not used
to fit the new gate. The holdout tests transfer across selector and mode
condition, not wholly untouched payload bytes.

| Mode scenario | Old gates, call errors | Old gates, answer errors | New frozen gates, answer errors | Answer handoff |
| --- | ---: | ---: | ---: | --- |
| Held `81` | 21/64 | 18/64 | **0/64** | Exact eight line and eight decoded controller bytes |
| `81→A1` | 13/64 | 10/64 | **0/64** | Exact eight line and eight decoded controller bytes |

The new answer runs use the actual PROM dumps and an unchanged executed
8031 receiver probe after the modeled external-sync 8251. They see no
unseen phase states; all eight answer bytes match the independently offered
payload, with no modeled controller errors and 2,961 microcycles of minimum
setup before the first RxC edge. This is a useful **conditional C3 result**
under the direct-mode, capture, line and USART assumptions. It does not
identify an onboard DSC phase decoder or the physical serial route.

The [mode-gate audit](joint_mask04_12a_mode_gate_merge_audit.py) prevents
overgeneralizing the new gate. In the earlier `01`-mode development graph,
state `09` requires phase 3; in the call-side held-`81` graph it requires
phase 2. A single phase function of only the seven captured bits cannot
satisfy both labels. An assumed `3EB` bit 7 can select between the old
`01` and new `81/A1` gates: this conditional mux is exact on eight saved
`01`-mode receive streams, both call-side mode-development streams and both
answer-side mode-condition holdouts. The bit-7 net and mux are **not
observed board connections**. Carrier offset or another missing signal could also
explain the conflict; the current runs do not isolate mode from every
other condition. The new gate alone makes 14–20 errors on the phase-88
`01`-mode streams and must not replace the old gate globally.

The [full-run report](results/joint-mask04-12a-row-mode-edge.json),
[answer holdout](results/joint-mask04-12a-mode-phase-holdout.json) and
[mode-gate audit](results/joint-mask04-12a-mode-gate-merge-audit.json)
save trace digests, gate terms, state labels, wrong indices, bytes and
source hashes. Reproduce from the microcode directory with:

```sh
python3 g2/joint_mask04_12a_row_mode_edge.py
python3 g2/joint_mask04_12a_mode_phase_holdout.py
python3 g2/joint_mask04_12a_mode_gate_merge_audit.py
```

C3 remains open and G2 active. Challenge the conditional mode gate on a
fresh payload/carrier phase and test whether a photo-compatible `3EB` bit-7
route could actually select the phase logic and the RxD/SYNDET serializer.
