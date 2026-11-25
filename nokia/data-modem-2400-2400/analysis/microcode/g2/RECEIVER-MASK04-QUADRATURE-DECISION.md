# Raw mask-04 retained bytes do not give a fixed-phase quadrature decision

The [direct retained-bit screen](RECEIVER-MASK04-RETAINED-BIT.md) found no
received bit in individual R1, R12 or Q bits. This diagnostic asks whether
any *pair* of those bytes behaves like in-phase and quadrature components
at one fixed symbol phase. It runs eleven independent real-PROM receive
streams under the same mask-`04` field map, four-row dispatch, inverted
previous-overflow TEST and complementary ADC schedule. Three streams train
the choice, four hold it out and four fresh streams check the selected
choice. Each stream selects 6,000 ADC bytes and captures R1/R12/Q after
every `3FE`.

For each of the three register pairs, the screen tries offset-binary and
two's-complement interpretation of each byte, optional quadrature
conjugation, optional carrier half-turn, all 375 table-visit phases per
symbol and lags −2…+2. It computes an **external** differential quadrant
from adjacent symbol samples and maps it to the reference dibit. None of
the 90,000 fixed choices fits the 36 training dibits exactly. The best
training choice, R1/Q at phase 141 with lag +1, makes 19/36 training errors and
25/48 holdout errors; six holdout decisions are undefined because the
complex differential product is zero. It makes 39/48 errors across the
four fresh streams, with six undefined decisions.

This rules out a simple fixed-phase raw-byte I/Q interpretation in this
fixture. It does not rule out filtering, a different latch phase or data
source, adaptive carrier recovery, or another field/input mapping. The
quadrant calculation is a diagnostic outside the DSC, not an executed
microcode decision. No result identifies USART 01 RxD, so C3 remains open.
Use the [executed arithmetic check](JOINT-MASK04-ADC-ROM-WRAPPER-RULE.md)
to guide the next stateful readout or output-route experiment.

The [machine report](results/receiver-mask04-quadrature-decision.json) saves
the search, independent-stream scores, trace digests and source hashes.
Reproduce with `python3 g2/receiver_mask04_quadrature_decision.py` from
the microcode directory.
