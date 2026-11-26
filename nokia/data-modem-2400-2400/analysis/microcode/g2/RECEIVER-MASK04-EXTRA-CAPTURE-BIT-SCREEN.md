# One more capture bit does not simplify the tested receive readout

The [four-bit transition readout](RECEIVER-MASK04-TWO-VISIT-TRANSITIONS.md)
uses executed `3F8` Y6/Y7 at ADC visits 47 and 94 as a symbol state.
This [screen](receiver_mask04_extra_capture_bit_screen.py) adds exactly
one Y4 or Y5 bit from either visit and asks whether the extra bit gives
a compact, better-covered state transition rule. Y0–Y3 are constant in
these saved captures, while Y6/Y7 are already in the baseline.

The eight intermediate-angle, seed-`726C` real-PROM streams are the
**only training data** for each lookup and its forced cubic predictions.
The separate seed-`E217`, 13-angle streams supply 611 independent
differential decisions. Neither their labels nor their keys enter the
fit. Each stream comes from saved executed PROM captures; this screen
does not rerun the microcode.

| Symbol state | Training keys | Held-out wrong / unknown / 611 | Held-out data unknown | Quadratic contradictions after combining both datasets |
| --- | ---: | ---: | ---: | ---: |
| Y6/Y7 at both visits | 58 | 0 / **84** | 42 | 35 |
| Add visit-47 Y4 | 92 | 0 / 169 | 93 | 6 |
| Add visit-47 Y5 | 72 | 0 / 196 | 74 | 37 |
| Add visit-94 Y4 | 89 | 0 / 151 | 105 | 6 |
| Add visit-94 Y5 | 87 | 0 / 122 | 80 | 31 |

The independent scores include a label only when the development lookup
contains the transition or **every** degree-three Boolean rule fitting
that lookup forces the same label. No candidate makes a wrong known
decision, but each added bit leaves more unknowns than the four-bit
baseline. The quadratic counts are a separate structural screen after
both datasets have been combined; they are **not** held-out scores. Even
the best Y4 additions leave six contradictory transition keys, so none
is a simple degree-two rule over these captures.

This rejects the narrow idea that one unmotivated extra Y4/Y5 latch bit
will repair the sparse four-bit readout or reveal a compact quadratic
decision circuit. It does not reject the DSC receiver or the later
[dual-feature consensus](RECEIVER-MASK04-DUAL-FEATURE-CONSENSUS.md),
which uses more development data and a different pair of features.
The next receive test should apply the existing
[raw-PROM `3F8→3F9` clock candidate](RECEIVER-MASK04-3F8-TRANSIENT-BIT.md)
to an explicit one-bit latch, including its startup `18C` edge, and test
when a later `3ED` consumer can use the held value. The latch,
serializer and USART route remain assumptions. C3 stays open without
waiting for continuity.

The [machine report](results/receiver-mask04-extra-capture-bit-screen.json)
records every variant, trace digest and source hash. Reproduce from the
microcode directory with
`python3 g2/receiver_mask04_extra_capture_bit_screen.py`.
