# The joined fixed readout is sensitive to gain and ADC bias

The [complete zero-run handoff](JOINT-MASK04-FULL-ZERO-HANDOFF.md) recovered
all eight line bytes at the nominal modeled signal level using the frozen
`46/93` receive pair. This [challenge](joint_mask04_full_zero_analog_variants.py)
reconstructs each 838-bit Y7 source waveform from the verified R1 phase
recurrence and requires its SHA-256 hash and six post-A4 bits to match the
saved **real-PROM transmitter run**. Its reconstructed nominal PCM also
hash-matches the prior joined fixture. Only then does it alter the signal
presented to the receiver: multiply its PCM by 0.75 and add either +16
or −16 counts before the hypothetical complementary ADC. Each of four
variants executes **768,047 real-PROM receive instructions** with the
same frozen capture pairs and ADC-margin selector.

| Selector | PCM bias | Independent reference errors | Frozen 46/93 wrong / unknown data dibits | ADC-margin wrong / unknown data dibits |
| --- | ---: | ---: | ---: | ---: |
| `40` call | +16 | 0 | 0 / 14 | 1 / 4 |
| `40` call | −16 | 0 | 1 / 17 | 1 / 7 |
| `60` answer | +16 | 0 | 0 / 19 | 0 / 9 |
| `60` answer | −16 | 0 | 3 / 17 | 3 / 6 |

All counts are among 32 A4 data dibits. The independent known-carrier
reference receiver still decodes every waveform, so the failure is in
the present executed-byte readout hypothesis, not a loss of the modeled
transmitted information. None of the four variants produces all eight
line bytes from the frozen `46/93` rule, and no missing decision was
filled from the expected answer or passed to the 8031. This prevents
generalizing the nominal full-chain result to modest gain/bias changes.

The experiment does not establish whether the Nokia board normalizes
ADC levels, changes thresholds, tracks phase or uses a different output
source. Gain, DC offset, ADC coding and analog filter are external
fixtures; receiver input and decision wires remain untraced. C3 stays
open. A useful next run should look for executed state that tracks input
gain or midpoint, then test a predeclared adaptive rule on fresh
waveforms and a controller-byte handoff.

The [machine report](results/joint-mask04-full-zero-analog-variants.json)
records each signal/ADC hash, PROM trace digest and decision score.
Reproduce from the microcode directory with
`python3 g2/joint_mask04_full_zero_analog_variants.py`.
