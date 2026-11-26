# What the sampled receive Y bytes actually contain

The [complete receive-state corpus](JOINT-MASK04-FULL-BUS-RECEIVE-STATES.md)
made it possible to test whether the two most-used external readouts are
seeing DSC demodulator state or simply quantized input samples. The six
real-PROM traces cover call and answer non-zero payloads at −7, 0 and
+7 Hz under the same labelled full-byte DAC, line, AGC and ADC fixture.

At all **3,900 captured `3F8` visits**—ten visits per symbol, 65 symbols
per case—executed Y is exactly `(ADC & 0xF0) | 0x0F`. The upper nibble is
the modeled ADC high nibble and the lower nibble is constant `F`. The
two Y sign bits used by a candidate `47/94` quadrant slicer therefore
match the corresponding raw ADC sign bits for every symbol. The earlier
[arithmetic trace](JOINT-MASK04-ADC-ROM-WRAPPER-RULE.md) already checked
the general `3F8` equation and the next real-ROM read at `3F9`; this
result identifies its simplified value in these full-byte fixtures.

At three ADC sample boundaries per symbol, the `3ED` bytes also have a
specific observed relationship. Across **1,170 boundary observations**
and 126 distinct adjacent quantized-sample pairs, row-0 Y at the first
visit after a boundary is a single-valued function of the **preceding**
ADC high nibble (14 observed codes); row-3 Y at that visit is a
single-valued function of the **current** high nibble (15 observed
codes). Both observed codebooks have zero conflicting inputs across the
six cases and three boundary positions. Each preceding code occurs with
6–11 different current codes, and each current code with 2–11 preceding
codes; the separation is therefore exercised by varied sample pairs.
The reversed dependencies fail: every current-code group has multiple
row-0 outputs, and 14 preceding-code groups have multiple row-3 outputs.

These findings explain why a sign-based or two-row external decoder can
appear to recover dibits: at the captured sites it is operating on one
or two quantized analog samples. **That alone does not demonstrate that
the microprogram made a receive decision.** The `3F9` ROM lookup and
the executed Q/RAM updates remain real, input-dependent computations;
the sampled-byte identity does not characterize their later state or
rule out an untraced downstream demodulator output. It does rule out
using *these direct Y-byte readouts* as independent evidence of such a
decision under the tested fixture.

The next C3 test should compare a candidate downstream Y/Q/RAM or latch
site with controls that hold the current ADC nibble fixed while changing
the preceding sample/history, and then seek a causal bit stream reaching
USART-01. Keep the physical route assumptions labelled and G2 active.

Run `python3 g2/joint_mask04_full_bus_3f8_adc_equivalence.py` and
`python3 g2/joint_mask04_full_bus_row_boundary_map.py` from the microcode
directory. The [ADC identity report](results/joint-mask04-full-bus-3f8-adc-equivalence.json)
and [row-boundary report](results/joint-mask04-full-bus-row-boundary-map.json)
record every score, observed codebook, source hash and limitation.
