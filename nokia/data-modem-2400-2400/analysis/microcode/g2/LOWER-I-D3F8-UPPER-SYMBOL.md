# The upper-sensitive ADC loop has no simple fixed-phase dibit bit

The [candidate upper-slice D route](LOWER-I-D3F8-UPPER-D-ROUTE.md) makes
the upper nibble of a held complementary ADC sample affect modeled state
and ROM addresses. The [symbol screen](lower_i_d3f8_upper_symbol_screen.py) asks
whether one of its recurring state bits is already a receive decision. It
executes the real PROMs under the same U8 I0←U17 bit 6 and inverted
previous-sign hypotheses for six periodic and four seeded nonperiodic
16-dibit streams. The independent reference receiver recovers every
stimulus. In each detailed run, the screen verifies all **24,000** offered
D3F8 bytes are selected by the ALU and that the upper instruction at the
input site is `FD`.

At every D3F8 visit it captures Y at `3F8`, `3F9` and `3FA`, Q, and all
16 RAM bytes after `3FA`. It tests each bit of these **20 channels** at all
**1,500 fixed visit phases** of a symbol, both polarities and symbol lags
from −2 to +2. A second family tests the same bits after subtracting the
previous symbol's byte at the same phase, modulo 256. Symbols 2–13 give
36 training checks across three periodic patterns, 36 periodic holdout
checks across three other patterns, and 48 nonperiodic holdout checks.

| Readout | Dibit bit | Fewest training errors / 36 | Exact training fits | Selected low-training candidate: train / periodic holdout / nonperiodic holdout errors |
| --- | ---: | ---: | ---: | ---: |
| Direct or inverted state bit | 0 | 1 | 0 | 4 / 9 / 16 |
| Direct or inverted state bit | 1 | 2 | 0 | 3 / 4 / 16 |
| Symbol-to-symbol byte subtraction bit | 0 | 3 | 0 | 4 / 9 / 20 |
| Symbol-to-symbol byte subtraction bit | 1 | 2 | 0 | 3 / 13 / 21 |

The [saved report](results/lower-i-d3f8-upper-symbol-screen.json) records
the selected candidate fields, training and holdout errors, trace digests
and source hashes. The table's selected candidate is the best combined fit
among rules with at most four training errors; its errors are not a
recovered-bit result. No rule in these two families fits even the training
set exactly. The richer upper-slice response therefore supplies **input
processing evidence**, but no direct dibit decision in this search.

This does not test a two-bit code, a nonlinear or matched-filter decision,
another output site, or a separately clocked latch. All wiring and clock
hypotheses remain unverified, and no signal has been tied to USART-01 RxD.
The next receiver experiment should constrain a *small* code or operation
from the microinstruction behavior, then validate it on the nonperiodic
streams and a candidate physical output route.
