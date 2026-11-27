# Revised package-capacity route for the receive phase bits

The nine-bit state combines first `3F8` Y5–Y7, second `3F8` Y7/Y4/Y6,
row-0 Y0/Y1, and later `3F8` Y4. Call these `s0`–`s8` in that order.
The candidate storage schedule uses photographed U14 LS75, U12 LS175,
and U3 LS373. U14 and U12 supply both Q and complementary Q outputs,
so six needed negative literals can come directly from their assumed
captured bits; U13 LS04 inverts only U3's `s3` and `s5` outputs.
[TI LS75](https://www.ti.com/product/SN74LS75) and
[TI LS175](https://www.ti.com/product/SN74LS175) document those
complementary outputs. The board traces to these pins remain unconfirmed.

One complete **logical** route uses U13 (2 of 6 inverters), U15 (its
4-2-3-2 AOI), U19 (3 of 3 three-input NANDs), and U21 (3 of 4
two-input NORs):

```text
U19a = NAND(s2, ~s5, s7)
U19b = NAND(~s2, ~s7, ~s8)
U21c = NOR(U19b, U19b)             # ~s2 & ~s7 & ~s8
U15Y = NOT[(~s1 & s3 & s7 & s8)    # four-input arm
           + (~s2 & ~s3)           # two-input arm
           + (~s0 & ~s1 & ~s6)     # three-input arm
           + (U21c & HIGH)]        # two-input arm
P0   = NAND(U15Y, U19a, HIGH)
U21a = NOR(~s6, s7)
P1   = NOR(~s2, U21a)              # U21b
phase = P0 + 2*P1                  # global offset +1
```

The earlier circuit differed only in U15's two-input arm: it used
`s1 & ~s3`. Frozen on 42 development streams, that circuit predicted
new state `0F5` correctly on both carrier-`161` streams, recovering
all 64 dibits, exact modeled line bytes, and exact executed-controller
payloads. It predicted `101` and `141` incorrectly on carrier `163`:
17/64 call and 13/64 answer dibits were wrong, and both line and
controller payloads were wrong. The controller's USART status-error
counter remained zero; it is **not** a payload-equality check. None of
these streams clipped in the modeled ADC.

The joined 46-stream phase graph has 45 codes and zero conflicts. It
assigns `101` and `141` relative phase 0, while the first circuit
predicted 3. Replacing the one U15 arm above fits all 45 labels and
all 2,944 saved dibit transitions. This is development evidence because
the failing carrier-`163` streams selected the revision.

The revised circuit was frozen before four fresh real-PROM/controller
streams at carrier starts `165` and `167`, each with new eight-byte
payloads at calibrated 1.0× receive gain. All four visit previously
unseen state `035`; each has **0/64 dibit errors**, exact modeled line
bytes, exact executed-controller payloads, and zero modeled clipping.
The independent reference decoder missed 1–3 dibits in these streams,
so the package-route result is tested against the offered controller
payload and real-PROM execution, not inferred from that reference.

The staged storage replay checks 50 streams and 3,250 symbols. First Y
is held at modeled cycle 1,535; U12 copies first Y6 and row-0 Y0/Y1 at
1,554; U3 holds second Y at 3,039; U14's reusable pair captures later
Y4 at 3,071. Row-0 Y0/Y1 never change between visits `46` and `47`,
and the staged nine-bit state matches every direct capture. The first
modeled RxC edge is at cycle 6,000, leaving 2,929 microcode cycles
after the last capture. This is a capacity and logical timing check,
not a measured electrical path.

Reproduce with `joint_mask04_12a_two_bit_package_route.py` (first
circuit), `joint_mask04_12a_two_bit_package_holdout.py` and
`joint_mask04_12a_two_bit_package_holdout_audit.py` (failure analysis),
then `joint_mask04_12a_two_bit_package_route2.py`,
`joint_mask04_12a_two_bit_package_route2_holdout.py`, and
`joint_mask04_12a_two_bit_package_latch.py` (revised circuit and staged
replay). Matching source-hashed JSON reports are in `results/`.

A matched **1.15× receive-gain challenge** keeps the same carrier-`165/167`
starts and controller payloads as the successful 1.0× holdout. All four
transmitter trace hashes remain identical; their receive PCM and PROM
trace hashes change. Each higher-gain stream reaches four previously
unseen nine-bit states (`091`, `0D1`, `125`, `1FD`) yet the **same frozen
package circuit** recovers 0/64 wrong dibits, exact modeled line bytes,
and exact executed-controller payloads, with no modeled clipping. The
joined 54-stream phase graph has one 50-state component and zero
conflicts; it assigns those four new states the phases predicted by the
gate. The staged latch state also matches all 260 higher-gain symbols,
with no row-0 Y0/Y1 change across the U12 clock. This is a matched
gain-transfer pass under the same circuit assumptions. The
[audit](results/joint-mask04-12a-two-bit-package-gain115-audit.json)
checks the paired hashes, new-key predictions and staged capture;
`joint_mask04_12a_two_bit_package_route2_gain115.py` reproduces the
real-PROM challenge.

This supplies a photo-package-compatible **candidate** capture and
phase-decision path with an independent unseen-state pass. Data and
enable nets, fan-out, tie-high points, analog line/ADC route, and the
DSC-to-USART connection remain assumed. The subsequent
[matched mode-boundary control](JOINT-MASK04-12A-TWO-BIT-PACKAGE-MODE-CONTROL.md)
rejects this fixed gate under held `81` and a later `81→A1` edge, while
identifying a photo-compatible early-Y4 capture alternative. C3 and G2
stay open; constrain the nets and challenge a revised frozen route.
