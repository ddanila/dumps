# The latched mask-04 nibble is not a fixed-phase DPSK decision

The [PROM-latch candidate](RECEIVER-MASK04-3ED-PROM-LATCH.md) captures
the R1-derived `3ED` Y byte after each receive row under a labelled U19
NAND hypothesis. Because R1 is the negative of Q's previous low nibble,
this screen tests whether Y[3:0] is a phase code from which a differential
dibit can be read. It uses eleven independent real-PROM streams under the
same mask-`04` field map, four-row dispatch, inverted previous-overflow
TEST and complementary ADC schedule. Seven streams supply three training
and four holdout cases; four fresh random streams check the training
selection. Each executes 192,047 instructions and captures 24,000 `3ED`
bytes, four per ADC-table visit.

For each of the 1,500 capture phases per symbol, the diagnostic subtracts
the previous symbol's four-bit value from the current value modulo 16,
tries both phase directions and all 16 fixed carrier/decision offsets,
rounds to the nearest quadrant, then uses the reference dibit order.
Lags −2…+2 produce 240,000 fixed choices. None fits all 36 training
dibits. The training-selected best uses reverse phase, offset 8, phase 4
and lag 0; it misses 10/36 training, 16/48 holdout and 10/48 fresh
dibits. The fresh scores are 3, 0, 5 and 2 errors, so one perfect fresh
stream does not generalize to the other three.

This excludes a single fixed-phase differential interpretation of the
captured nibble in this fixture. It does not exclude a multi-sample
filter, adaptive timing/carrier recovery, another data source or a
different field/input map. The phase subtraction and decision are
external diagnostics, not executed DSC code. The U19/U12 pins and USART
01 RxD route remain untraced, and C3 stays open. Continue from executed
four-row arithmetic or another photo-compatible output path rather than
assigning this nibble a demodulator role from its shape alone.

The [machine report](results/receiver-mask04-latched-nibble-phase.json)
records the search, trace and capture hashes, holdout/fresh scores and
source hashes. Reproduce with
`python3 g2/receiver_mask04_latched_nibble_phase.py` from the microcode
directory.
