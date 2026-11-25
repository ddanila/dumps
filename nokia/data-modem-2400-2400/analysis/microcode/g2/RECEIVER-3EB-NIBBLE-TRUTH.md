# The reached 3EB wrapper reads only the high D nibble

The [full ADC bus-hold screen](RECEIVER-3EB-ADC-ROUTE-SCREEN.md) made the
conditional `3EF/3F7` receive loop exit early. To test whether a grouped
buffer could gate only part of that bus, the
[nibble screen](receiver_3eb_nibble_truth.py) runs the first `3EB`/`3ED`
decision once for **every D byte, 00–FF**, then runs the 32-sample reference
waveform with several two-row `3EB` lane/enable patterns. These are explicit
untraced input hypotheses under the same joint mapping, Q/RAM seed and
inverted-previous-sign condition.

For all 16 low-nibble values in each high-nibble group, the first `3EB` Y
and `3ED` branch are identical. The executed relation is
`Y3EB = ((D >> 4) + 1) << 4 (mod 256)`. The first `3ED` test exits toward
`3EE` for D high nibble `6`, `A`, `B` or `F`; the other 12 classes return to
`3EA`. This is a **fixture-specific first-wrapper rule**, not a hardware
ADC encoding or full demodulator truth table.

| ADC presented at `3EB` | Reference-waveform `3F8` visits | Trace relation |
| --- | ---: | --- |
| Default `01` | 3,000 | Baseline |
| Full byte at both wrapper visits | 282 | Exits to `084` |
| Full byte at first visit only | 282 | Exits to `084` |
| Full byte at second visit only | 283 | Exits to `084` |
| Low nibble at both, first only, or second only | 3,000 each | **Bit-for-bit same trace digest as baseline** |

The low-nibble route cannot rescue a receiver interpretation: it is inert
under this field mapping. The full-byte route changes a real microprogram
loop decision but fails to sustain the tested waveform. A useful next
candidate must change the actual high-slice input/condition timing, dispatch
source, or a separately latched output while maintaining a continuous ADC
stream. Its physical bus and USART RxD route remain unverified. The
[machine report](results/receiver-3eb-nibble-truth.json) includes all 16
high-nibble classes, seven waveform runs, trace digests and the script hash.
Reproduce with `python3 g2/receiver_3eb_nibble_truth.py` from the microcode
directory.
