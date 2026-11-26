# The buffered line changes both `3F9` key coverage and key meaning

The [paired audit](joint_mask04_12a_3f9_key_audit.py) reruns the two
independent training carriers and both ROM-sensitive `12A` buffered
loopbacks. It records each symbol's eight ADC bytes and the executed
`3F9`/`3FA` Y bytes at visits 46/93. Independent and loopback trace,
ADC, and prior prediction hashes/checks match the saved experiments.
The frozen rule uses only bits 4–5 of each `3F9` byte and the preceding
symbol's corresponding state.

| Fixture | Data symbols with a key absent from training | Familiar keys with a wrong frozen label |
| --- | ---: | ---: |
| Call `40` buffered loopback | 24/32 | 3 |
| Answer `60` buffered loopback | 24/32 | 7 |

The original no-correct-readout gaps are call indices `8,14,29` and
answer indices `10,12,13,17,31`. Seven of their eight `3F9` transition
keys are absent from training. The exception is answer index `10`: key
`110` has frozen label `2`, but the offered dibit is `0`. Its captured
full `3F9` bytes are `78/28`, while the independent training occurrence
of key `110` captured `31/2D`; the two-bit projection maps both to the
same key. Two call gaps share unseen key `105` with dibit `1`, despite
different eight-byte ADC windows. Call index `29` and answer index `17`
share unseen key `169` with dibit `0`.

This locates a real limitation of the **frozen two-bit lookup**: sparse
key coverage is not the only issue; even an observed key can alias a
different dibit after the modeled line/ADC path. It does not show that
the complete `3F9` bytes or another executed feature cannot decode the
stream. The next test should retain more `3F9` bits or a short temporal
history, fit on independent legal carriers spanning gain and phase,
freeze the rule, then challenge it with new buffered payloads before
using it for the paced USART/8031 handoff. The DAC/ADC and RxD circuits
remain labeled hypotheses; C3 and G2 stay open.

The [machine report](results/joint-mask04-12a-3f9-key-audit.json)
contains every ADC octet, captured Y byte, key, label and gap flag.
Reproduce with `python3 g2/joint_mask04_12a_3f9_key_audit.py`.
