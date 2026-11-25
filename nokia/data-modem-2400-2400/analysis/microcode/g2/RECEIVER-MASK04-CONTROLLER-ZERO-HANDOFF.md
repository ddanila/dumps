# Conditional DSC receive stream reaches the controller's zero detector

The [joint replay](receiver_mask04_controller_zero_handoff.py) runs eight
scrambled zero octets through the continuous mask-`04` receive fixture,
then offers the recovered bytes to the unchanged 8031 ROM at its
state-`AF` USART-01 data reads. It uses both V.26 ter scrambler delays
and two carrier rotations. Each 64-symbol run includes 32 `11` reversal
preamble symbols followed immediately by 32 data symbols; no DSC state is
reset at the boundary. The reference waveform, complementary-ADC ingress,
phase readout and byte alignment remain labelled hypotheses.

| Scrambler delay | Carrier | Eight DSC-recovered line bytes | Data errors | 8031 result |
| ---: | ---: | --- | ---: | --- |
| 5 | 0° | `62 DE 61 9D 7C 5F E5 E2` | 0/32 dibits | eight decoded `00`; state `AF→B0` |
| 5 | 45° | `62 DE 61 9D 7C 5F E5 E2` | 0/32 | eight decoded `00`; `AF→B0` |
| 18 | 0° | `A5 C2 4C 58 52 47 65 B4` | 0/32 | eight decoded `00`; `AF→B0` |
| 18 | 45° | `A5 C2 4C 58 52 47 65 B4` | 0/32 | eight decoded `00`; `AF→B0` |

Each DSC run executes 768,047 real-PROM microinstructions and captures
24,000 candidate `3F8→3F9` edges. The selected readout also recovers all
31 measurable preamble dibits as `11`. The ROM-executed 8031 path reads
each offered byte via USART-01 status/data MOVX, descrambles it and counts
successive zero octets. At eight it enters `B0` and emits the previously
identified `D0 42 81 1A` frame. A control that flips the low bit of the
last offered line byte leaves state `AF`, resets the zero count and
emit `D0 42 89 9A`; the [machine report](results/receiver-mask04-controller-zero-handoff.json)
records the checked control and trace digests.

This joins an input-sensitive DSC execution to the controller's actual
receive routine under a concrete candidate serial handoff. It does **not**
show a physical 8251A RxD/RxC connection: an external readout forms the
bits, the byte boundary is assumed, and the probe supplies bytes at modeled
USART reads rather than clocking a physical or chip-level 8251A. The 8031
state-`AF` entry and state step are explicitly selected rather than reached
by a naturally timed main loop. C3 and C4 remain open. A next test can
vary the photo-compatible latch/RxC/RxD route and check the resulting bytes
against this controller signature without waiting for new continuity data.

The [external-SYNDET replay](RECEIVER-MASK04-EXTERNAL-SYNC-HANDOFF.md)
now adds a narrow bit-clock/RxRDY model before these same controller reads.
Mode `CC` requires an external SYNDET pulse; the earlier internal `FF` hunt
screen is counterfactual for this setup. The pulse source and wiring remain
assumptions, so C3 stays open.

Reproduce from the microcode directory with
`python3 g2/receiver_mask04_controller_zero_handoff.py`.
