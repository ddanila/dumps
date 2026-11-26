# Frozen six-bit receive transitions recover new payloads across gain and phase

The [sixth-bit development screen](JOINT-MASK04-12A-FROZEN-FIFTH-CHALLENGE.md)
found a 91-key, zero-conflict transition table using first `3F8` Y bits
5–7 and second Y bits 4, 6 and 7 at the assumed ADC visits 46 and 93.
This test freezes that feature and its table **before** offering a
third, previously unused eight-byte payload in each controller
selector mode. The real-PROM q3/mask-04 transmitter has a one-time
R1 offset `20` at mute start. Each resulting bus-0/Q=0.5/+6 line is
received at 75%, 100% and 125% of the fixed zero-run gain.

| Selector | New payload | All four data dibits present | Levels with exact 64/64 decisions and eight line bytes | Aligned modeled 8251/8031 result |
| --- | --- | --- | --- | --- |
| `40` | `0F 72 B5 C8 31 E6 4A 9D` | yes | 75%, 100%, 125% | eight exact decoded bytes, zero errors/overruns |
| `60` | `A6 19 F0 4D 83 2B C5 78` | yes | 75%, 100%, 125% | eight exact decoded bytes, zero errors/overruns |

The six executed receiver runs make **zero wrong and zero unknown**
decisions, recover the offered scrambled line bytes, and drive the
modeled 8251/unchanged 8031 to the exact new source payloads with
aligned assumed SYNDET. The independent fixed-carrier reference
decoder is also exact in all call cases; it makes two decisions wrong
in each answer case, while the DSC-derived rule remains exact. The
six-bit table is not refitted on any of these runs.

Every transition key encountered here was already among the 91
development keys. This is a clean new-**data** validation under
combined gain and phase change, but it does not test unseen keys,
other carrier starts, or noise. The two Y capture clocks, six-bit
state storage, transition logic, converter buses and serial wiring
remain photo-compatible assumptions rather than identified Nokia
connections. C2/C3/G2 remain open. Next vary carrier start phase
and timing with the rule frozen, and test a circuit built from
photo-compatible latches and logic without using payload labels.

The [machine report](results/joint-mask04-12a-frozen-sixth-new-payloads.json)
records each real-PROM trace digest, full Y captures, decisions,
controller handoff and source hashes. Reproduce from the microcode
directory with:

```sh
python3 g2/joint_mask04_12a_frozen_sixth_new_payloads.py
```
