# Whole-store PROM clock and parallel latch schedule on executed Tx traces

The [parallel-bus test](JOINT-MASK04-TX-PARALLEL-LATCH-BUS.md) found a
photo-compatible 74LS273 direct capture of settled `12A` Y, provided the
74LS373 does not drive conflicting shared Q lines before the sample
clock. This [integrated event replay](joint_mask04_tx_parallel_clock_schedule.py)
executes the real controller-fed PROM streams and tests one explicit
schedule. It uses the [four-literal whole-store decode](JOINT-MASK04-TX-12A-FULL-STORE-GATE.md)
`U11.D0 & U17.D1 & U17.D3 & ~U18.D1`, whose only selected address is
`12A`. The inverted select rises at the following `127`; an assumed
counter qualifies every 375th such edge. The 74LS273 captures the
previous `12A` Y before new `127` Y settles. The 74LS373 is assumed
transparent on the paired D inputs but output-disabled through that
clock window. Its outputs may stay disabled for the whole transmit run;
they may be enabled afterward only if its latch enable first closes on
the same byte before new `127` Y changes.

Each selector executes 1,248,256 PROM words, with the same trace hash as
the earlier call/answer run. There are 312,054 `12A` visits and 312,053
completed `12A→127` transitions; the final trace word is `12A` without
a following `127`. The counter selects 832 clocks, starting at modeled
cycle 44 and spaced **exactly 1,500 PROM cycles** apart. At a 14.4 MHz
microcycle clock, that would be 9,600 samples/s; the actual clock divider
and board clock net are still assumptions.

For both selectors, the captured 832-byte hash equals the previously
executed early `12A` stream. Clocking after `127` Y settles reproduces
the different late-control hash. The early stream retains zero saved
filtered A3/A4 errors on all six candidate DAC bus orders; the late
control has 0–1 call and 2–3 answer errors. If the 74LS373 output were
enabled before the clock, it would disagree with the old 74LS273 Q value
on 831/831 checked sample transitions per selector. The assumed disabled
window avoids that digital contention in the model.

The [source-hashed report](results/joint-mask04-tx-parallel-clock-schedule.json)
records clock cycles, trace/sample hashes and the output-enable control.
No photographed gate-to-counter, counter-to-clock, Y-to-D, OE or DAC08
pin net has been proven. The 74LS273 still requires at least 20 ns setup
and 5 ns hold around the clock; this replay does not measure the PROM,
gate, counter or Am2901 propagation ordering. Test those timing margins
or an independent DAC input/line observation under the same stimulus.
C2 and G2 remain active, and missing continuity does not block the
next conditional test.
