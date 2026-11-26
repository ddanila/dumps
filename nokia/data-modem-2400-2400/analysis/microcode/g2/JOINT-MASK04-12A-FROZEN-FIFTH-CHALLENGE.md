# New payloads expose a gain-plus-phase limit of the frozen five-bit readout

The [fifth-bit screen](JOINT-MASK04-12A-FIFTH-RECEIVE-BIT.md) found
three five-bit features that separated all earlier gain and phase
transition labels and decoded the controller A4/A5 holdout. This
challenge freezes the smallest table: first `3F8` Y bits 5–7 at
visit 46 and second Y bits 6–7 at visit 93, with its 55 development
transition keys. It offers two previously unused eight-byte
controller payloads through real-PROM q3/mask-04 Tx→line→Rx runs.
Both modes use the same one-time R1 offset `20` at mute start and
fixed bus-0/Q=0.5/+6 timing. Each is replayed at 75%, 100% and 125%
of the previously fixed line gain; no new transition label is fitted.

| Selector | Fresh payload | 75%: wrong / unknown | 100%: wrong / unknown | 125%: wrong / unknown |
| --- | --- | ---: | ---: | ---: |
| `40` | `7B A4 1D E2 56 C9 03 8F` | 19 / 5 | 0 / 0 | 0 / 27 |
| `60` | `91 2F D8 64 AB 05 73 CE` | 11 / 17 | 0 / 0 | 0 / 22 |

At nominal level the frozen rule recovers all 64 decisions and eight
line bytes per mode; aligned modeled 8251/unchanged 8031 handoff
descrambles the exact new payloads. At 75%, several **already trained**
transition keys demand different dibits, so merely filling unknown
keys cannot repair the rule. At 125%, the known decisions are correct
but many new keys abstain. Rechecking the other two previously
successful fifth-bit choices on the saved full-Y captures also finds
wrong and unknown decisions at changed levels. The earlier holdout
therefore did not establish combined gain/phase robustness.

An exploratory [sixth-bit screen](joint_mask04_12a_sixth_receive_bit.py)
uses the 14 now-labeled development runs to compare all twelve
single-bit and 66 two-bit extensions of the original four-bit state.
No single extra bit is conflict-free. Three two-bit choices are:

| Added bits | Distinct observed transition keys | Development conflicts | Reused controller A4/A5 check |
| --- | ---: | ---: | --- |
| First Y4 + second Y4 | 96 | 0 | 0 wrong, 0 unknown in both modes |
| Second Y4 + Y5 | 93 | 0 | same |
| Second Y4 + Y6 | 91 | 0 | same |

The controller A4/A5 stream was used in the previous fifth-bit
validation, so this is a **reused check**, not untouched evidence for
the new six-bit choice. The 91-key second-Y4/Y6 candidate is the
smallest observed table; it remains a labelled two-capture/logic
hypothesis. Next freeze it, then challenge genuinely new payloads at
combined phase/gain settings and test a photo-compatible latch and
decision circuit. C2/C3/G2 remain active; unknown wiring does not
block that experiment.

The [new-payload report](results/joint-mask04-12a-frozen-fifth-new-payloads.json)
records real-PROM trace digests, full Y captures, decisions and
controller results. The [sixth-bit report](results/joint-mask04-12a-sixth-receive-bit.json)
records all 78 feature screens and the reused controller check.
Reproduce from the microcode directory:

```sh
python3 g2/joint_mask04_12a_frozen_fifth_new_payloads.py
python3 g2/joint_mask04_12a_sixth_receive_bit.py
```
