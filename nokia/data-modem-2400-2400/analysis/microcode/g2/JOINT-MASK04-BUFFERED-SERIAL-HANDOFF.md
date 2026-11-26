# One-symbol buffered serial-to-D127 handoff

The [immediate second-bit-edge pulse](JOINT-MASK04-SERIAL-EDGE-PULSE.md)
missed data decisions. This experiment tests a causal alternative: latch each
completed pair of the controller's 2,400-bit/s TxD bits and issue its four-visit
`D127` pulse at the **next** 1,200-symbol/s boundary. The first A4 symbol
holds the final training dibit, so the data begins at bit 66 rather than 64.
There are 33 A4 symbols: one buffered training symbol and 32 data symbols.

Run `python3 g2/joint_mask04_buffered_serial_handoff.py` from the microcode
directory. The script drives the real DSC transmitter PROM for 1,269,256
microcycles per selector, uses the candidate Y7-to-B5 latch/line and ADC
fixture, drives a separate real DSC receiver PROM for 780,047 words per
selector, applies the previously frozen 46/93 readout, then sends the
recovered bytes through the paced 8251 and unmodified 8031 ROM. It saves
[the full trace summary](results/joint-mask04-buffered-serial-handoff.json).

| Controller selector | Reference errors | Frozen 46/93 errors/unknown, 64 checks | Recovered line bytes | Aligned SYNDET |
| --- | ---: | ---: | --- | --- |
| `40` call | 0 | 0/0 | `62 DE 61 9D 7C 5F E5 E2` | `AF→B0`, eight zero octets |
| `60` answer | 0 | 0/0 | `A5 C2 4C 58 52 47 65 B4` | `AF→B0`, eight zero octets |

Both runs preserve the earlier A1–A3 PROM Y7 prefix. The controller consumes
the exact eight recovered bytes with no overrun or emulator error. Moving
SYNDET from bit 66 to 65, 67 or 130, or using the opposite selector, leaves
the controller at `AF`. The frozen ADC-margin selector is **not** equivalent
on this fixture: it makes one call error at symbol 45, while the fixed 46/93
readout is exact. This is a useful independent challenge of the readout rule.

This establishes a complete **conditional** serial-bit-to-D127-to-PROM-to-
PROM-to-controller execution for the zero-run payload. The paired-bit latch,
pulse counter and mask, DAC/ADC nets, analog line, sample clocks and SYNDET
source remain hypotheses. The frozen decision rule is an external diagnostic,
not a demonstrated on-board USART drive. The processors were run sequentially
under a paced interface model. Thus C2 and C3 stay open. The next tests should
constrain the buffered pulse source, candidate DAC/ADC route and USART
decision/clock/sync circuit with the available photographs and independent
timing cases. Missing continuity does not block those tests.
