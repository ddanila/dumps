# A previous-carry TEST hypothesis sustains high-nibble RAM feedback

The [condition replay](joint_mask04_ram_condition_rescue.py) revisits the
[high-nibble `3FA` return exit](JOINT-MASK04-RAM-HIGH-RETURN-EXIT.md).
That exit occurred under an assumed **previous-overflow** TEST source.
The photographed condition multiplexer does not establish its input
selection or flag timing, so this screen runs all sixteen combinations
of previous/current timing, zero/sign/carry/overflow flag and polarity
on the same legal 64-sample reference waveform. Each case requests
96,047 real-PROM words and 3,000 ADC selections.

Without feedback, only three combinations sustain all 3,000 ADC visits:
previous sign, carry and overflow, each with polarity 1. All other
thirteen take `3ED→3EE` before the first ADC selection in this waveform.
The earlier short held-input screen had five survivors; its four
current-flag choices do not generalize to this legal varying input.

The three sustained controls then receive the **same** sample-paced
high-nibble RAM hypothesis: `3F9` Y high nibble is written at `3EC`,
returned from three samples behind into `3FA` D high nibble, and writes
freeze after sample 25. All three first read noninitial `21` at cycle
4,577, but their control flow differs:

| Previous flag, polarity 1 | ADC visits with feedback | Loop exits |
| --- | ---: | ---: |
| Sign | 236 | 1 |
| **Carry** | **3,000** | **0** |
| Overflow | 939 | 1 |

Thus the previous-carry TEST choice rescues this high-return route as a
*sustained execution candidate*. It does not establish the TEST pin or
external-RAM wiring, and a continuous loop alone is not echo
cancellation. The next [own/remote/mixed challenge](JOINT-MASK04-RAM-CARRY-ECHO-SCREEN.md)
tests whether the surviving route selectively reduces a candidate
echo response.

The [machine report](results/joint-mask04-ram-condition-rescue.json)
contains all nineteen baseline/feedback runs and trace hashes. Reproduce
from this directory with
`python3 g2/joint_mask04_ram_condition_rescue.py`.
