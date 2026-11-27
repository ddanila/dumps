# Later paced A5 data also passes the frozen thirteen-bit receive route

The [A4 replay](JOINT-MASK04-PACED-A4-THIRTEENBIT.md) used the first
eight aligned line bytes from a 17-character, uninterrupted 8031/8251
TxD execution. This [A5 challenge](joint_mask04_paced_a4_thirteenbit.py)
keeps the same frozen thirteen-bit gate, q3/mask-`04` PROM mapping,
carrier offset 203, 0.85× receive gain, candidate DAC bus, Q=0.5 line
filter and late mode edge. It substitutes the **next eight aligned
bytes** from that same paced controller execution:

| Selector | Later paced A5 line bytes | Independent reference errors | Frozen gate errors |
| --- | --- | ---: | ---: |
| Call `40` | `FE 82 75 F5 96 EE A0 70` | 1/64 (index 60) | **0/64** |
| Answer `60` | `6C 0E 36 91 14 18 8A DA` | 2/64 (indices 58, 61) | **0/64** |

Both real-PROM transmitter/receiver runs sustain, reproduce all eight
line bytes at the modeled 8251 receive port, and deliver the eight
independently predicted receiver-probe bytes from the unchanged 8031
ROM. Neither waveform clips or raises a modeled controller status
error. Both reach `1909`, absent from the original 159-state gate fit;
the frozen gate predicts its phase correctly. The A1 tone still peaks
at 2,100 Hz. The independent reference errors underline that this is
an executed-state decoder result, not a reference-decoder score.

The [call report](results/joint-mask04-paced-a5-thirteenbit.json) and
[answer report](results/joint-mask04-paced-a5-thirteenbit-answer.json)
are source-hashed. The controller source is continuous across A4 and
A5, but these two DSC replays **restart** their Tx/Rx state before the
selected eight-byte block. They therefore do not yet prove the
physical or modeled A4→A5 transition in one DSC run. The receive
probe starts at history `5A1234`; its decoded bytes are not claimed to
be the transmitting controller's original A5 plaintext. TxD pairing
and the DAC/ADC/analog, capture, gate and serial nets remain assumed.
C2, C3 and G2 stay open. Next run the 16 aligned A4+A5 bytes
continuously through the frozen thirteen-bit receive route and check
the boundary without refitting.
