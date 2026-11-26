# Preamble-calibrated analog normalization restores the joined readout

The [full-byte level challenge](JOINT-MASK04-FULL-BUS-LEVEL-CHALLENGE.md)
left wrong and unknown receiver decisions at 0.75 PCM gain plus ±16 counts
of bias, even though the independent decoder remained exact. This follow-up
tests one explicit **external AGC/midpoint circuit hypothesis**. Its target
midpoint and AC RMS come from the first 128 A3 samples of the modeled
nominal **call** waveform. Each changed stream estimates its own midpoint
and RMS from its first 128 received A3 samples. Those acquisition samples
remain uncorrected; only later samples are transformed to the fixed target.
No expected dibit or payload byte is used to estimate the correction.

The full real-PROM transmitter runs are repeated, and each altered PCM
stream must hash-match the saved level challenge before normalization.
Each corrected case
then executes 780,047 real-PROM receiver instructions with the same
frozen 46/93 and margin tables and the previously committed fixed-first
fallback. The target midpoint is −0.09375 PCM counts and target AC RMS is
52.509 counts; the four source estimates yield gain ratios 1.3335–1.3339.

| Selector | Input change | Uncorrected fallback wrong/unknown data dibits | Corrected frozen 46/93 wrong/unknown | Corrected fallback wrong/unknown | Recovered line bytes |
| --- | --- | ---: | ---: | ---: | --- |
| `40` call | 0.75 gain, +16 | 3/3 | 0/3 | 0/0 | `62 DE 61 9D 7C 5F E5 E2` |
| `40` call | 0.75 gain, −16 | 6/9 | 0/3 | 0/0 | same |
| `60` answer | 0.75 gain, +16 | 4/6 | 0/5 | 0/0 | `A5 C2 4C 58 52 47 65 B4` |
| `60` answer | 0.75 gain, −16 | 8/8 | 0/5 | 0/0 | same |

The independent reference decoder also remains exact in all four corrected
cases. The mean absolute corrected-versus-nominal PCM difference is
4.06–4.76 counts over the entire stream, including the deliberately
uncorrected acquisition interval. This shows that a simple, training-based
analog normalization is **sufficient under these four modeled affine level
changes** to restore the conditional joined receive path.

The candidate AGC is not an identified DSC instruction sequence or traced
board circuit. Its target amplitude is a modeling choice derived from the
nominal call fixture, not a measured ADC setpoint. The DAC/ADC nets, analog
gain control, decision gates, sample clocks and USART route remain
hypotheses. Freeze this correction now and challenge it on separate
non-zero payloads and phase/noise cases. C3 and G2 stay open and active.

Run `python3 g2/joint_mask04_full_bus_agc_candidate.py` from the
microcode directory. The [machine report](results/joint-mask04-full-bus-agc-candidate.json)
stores the learned moments, PCM/ADC hashes, PROM trace digests and every
decision score.
