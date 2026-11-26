# Separated PROM edges for the candidate row latch and counter

The [two-edge execution](joint_mask04_12a_row_clock_two_edge.py) tests a
photo-compatible way to select row 0 without changing U24 at the U12 latch
edge. It re-runs the full real-PROM receiver on both phase-112 controller-fed
payloads and checks each receiver trace digest and ADC hash against the
earlier [all-row execution](JOINT-MASK04-12A-ALL-ROW-PHASE112.md).

The previously identified all-positive three-bit raw-PROM decode
`U11.D7 & U17.D3 & U18.D5` selects `3ED` on these receive traces. A
second candidate decode, `U11.D7 & U17.D0 & U18.D6`, selects `3EA`.
Their assumed NAND rising edges are separated by one microcycle:

| Candidate event | Call `40` | Answer `60` |
| --- | ---: | ---: |
| Capture gate high only at `3ED`; falling at `3ED→3EA` | 97,500 | 97,500 |
| Counter gate high only at `3EA`; falling at `3EA→3EB` | 97,501 | 97,501 |
| Row-0 values retained under modulo-four qualification | 24,375 | 24,375 |

The extra `3EA` counter edge precedes the first observed `3ED` row and is
ignored until the assumed counter phase is established. After that, a
counter starting at `00` for row 0 selects every fourth `3ED→3EA` capture,
then increments at `3EA→3EB`. No overlapping high gate levels or row-phase
drift occur in either complete trace. All selected row-0 bytes at visits
46, 47, 93 and 94 match the independently saved all-row snapshots.

This is a **logical timing candidate**. The raw PROM values and executed
address sequence support both pulse locations, but do not show that these
decodes feed the photographed gates, U24 or U12. U24's reset/entry phase,
propagation delays, clock pulse widths and setup/hold margins remain
unmeasured. A one-microcycle separation avoids a same-edge logical race;
it does not prove electrical timing. The DAC, analog line, ADC and USART
routes are still labelled assumptions. C3 and G2 remain open and active.

The [machine report](results/joint-mask04-12a-row-clock-two-edge.json)
contains the two gate literals, full-trace counts, selected-value hashes and
source hashes. Reproduce from the microcode directory with:

```sh
python3 g2/joint_mask04_12a_row_clock_two_edge.py
```

Next vary the assumed U24 initialization and test whether a natural
controller/microcode mode transition resets or preserves the required row
phase; compare its selected row sequence with the same frozen phase gate.
