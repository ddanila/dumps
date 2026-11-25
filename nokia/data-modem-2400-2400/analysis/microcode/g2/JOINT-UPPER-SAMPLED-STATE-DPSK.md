# Sampled `Y3F8` retains a distorted receive waveform, not a decoded bit

The [five-visit pulse test](JOINT-UPPER-ADC-PULSE-MEMORY.md) shows that the
joint map's receive state has a repeatable timing phase. The
[sampled-state screen](joint_upper_sampled_state_dpsk.py) asks whether a
small, explicit readout of that state still carries a DPSK waveform. It
executes the real control and Am27S31 PROMs under the same ADC and upper
instruction hypotheses, then samples one reached state byte at five
adjacent visit phases near the start, center or end of each 188/187-visit
ADC hold. The eight channels are Y at `3F8–3FA`, Q and RAM 10–13. Each
byte is interpreted as offset binary or two's complement and passed to
the **independent known-carrier reference receiver**. This receiver is a
diagnostic outside the DSC model.

The screen tests 1,200 channel/phase/coding/symbol-lag candidates on seven
periodic and nonperiodic streams. Two periodic and one nonperiodic stream
provide 36 training decisions; another periodic and three nonperiodic
streams provide 48 holdout decisions. Sixteen candidates fit training
exactly, but **none** fits both training and holdout. The best combined
candidate is offset-binary `Y3F8` sampled at the center of each ADC hold:
0/36 training errors and 7/48 holdout errors.

That readout was then fixed and tested on four new seeded nonperiodic
streams. It makes **1, 7, 2 and 3 errors** in 12 checked decisions per
stream. Its sample correlation with the injected reference PCM is negative
and ranges from −0.78 to −0.60. Feeding the unmodified complementary ADC
samples to the same external receiver gives **0/48** errors on those four
streams. Thus `Y3F8` retains substantial waveform information but is a
distorted intermediate value; the screen provides no recovered DSC bit
and no improvement over the input signal. The [saved report](results/joint-upper-sampled-state-dpsk.json)
contains the fixed readout, all validation scores, trace digests and
source hashes.

The `D3F8` instructions subtract an internal operand from D in the
candidate map, which makes this signal-like result plausible. The
subtraction's physical role is still open: no residual was shown to fall
during echo training, and no readout was traced to USART RxD. A next
experiment should use paired local-echo and remote-signal inputs under a
mode-labelled scenario, or find a separate decision/output latch; this
external decoder cannot be counted as DSC demodulation.

Reproduce with:

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/joint_upper_sampled_state_dpsk.py
```
