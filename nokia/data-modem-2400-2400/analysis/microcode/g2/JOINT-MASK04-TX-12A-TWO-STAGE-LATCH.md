# A two-stage latch can preserve the settled `12A` byte until a later DAC clock

The [two-stage replay](joint_mask04_tx_12a_two_stage_latch.py) tests a
photo-compatible continuation of the [74LS373 beside the 74LS273 and
DAC08](DAC08-OUTPUT.md). In this **assumed** circuit, the 74LS373 is
transparent only while `U11.D0 & U17.D1` selects `12A`; it follows settled
`12A` ALU Y, then closes on `12A→127`. A counter selects every 375th later
74LS273 clock. This isolates the stored byte from the new `127` ALU output,
so the 74LS273 need not clock before `127` Y settles as in the earlier
[direct-latch timing test](JOINT-MASK04-TX-12A-DELAYED-LATCH.md).

A positive three-bit raw-PROM decode, `U11.D6 & U17.D0 & U18.D2`, is high
only at `127` among the 39 addresses reached in the tested transmitter mode.
A NAND of these bits rises on all 1,014 observed `127→128` transitions in
the 4,096-cycle screen. No one- or two-literal decode isolates `127` there.
The proposed decode is high at seven words in the full 1,024-word store,
so its exclusivity is mode-specific. The photo establishes neither this
gate wiring nor a counter-to-74LS273 clock route.

Four new uninterrupted executions (call/answer × upper/lower Am27S31 bank)
each run 1,248,256 real-PROM words. Their trace digests and both proposed
sample streams match the earlier bank/timing replay. The bank intervention
changes only the active ROM region; control flow remains equal.

| Selector | Hold `12A` through `127→128` clock: changed samples / 832 | Keep 74LS373 transparent through `127`: changed samples / 832 |
| --- | ---: | ---: |
| Call `40` | **198** | 0 |
| Answer `60` | **202** | 0 |

The hold stage therefore offers a concrete way for a **later** 74LS273
clock to carry the bank-sensitive `12A` byte. The transparent-through-`127`
control loses that byte, as predicted. The held output is byte-for-byte the
early `12A` sample stream from the prior run, so its conditional tone,
segment-1 reversals and dibit phases are those measured in the
[full-byte phase replay](JOINT-MASK04-12A-FULL-BUS-PHASE.md). This is not
an independent signal validation or a C2 pass: the 74LS373 D/LE/Q pins,
74LS273 D/CLK pins, divider, DAC08 bus and analog line path remain untraced.
Different propagation or output-enable timing may reject this route.

The [machine report](results/joint-mask04-tx-12a-two-stage-latch.json)
contains the gate census, all trace and sample hashes, ROM-bank contrasts
and source hashes. Reproduce from the microcode directory with:

```sh
python3 g2/joint_mask04_tx_12a_two_stage_latch.py
```
