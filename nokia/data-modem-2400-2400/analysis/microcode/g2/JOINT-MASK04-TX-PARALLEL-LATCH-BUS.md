# A parallel latch bus can capture `12A` Y, but needs output arbitration

The [front-side pin audit](PHOTO-DED-LATCH-BUS.md#pin-function-audit-of-the-visible-tracks)
suggests four 74LS273 D5–D8↔74LS373 D4–D1 links and four matching Q↔Q
links. These eight tracks are **not** a visible 74LS373 Q→74LS273 D serial
chain. This [real-PROM replay](joint_mask04_tx_parallel_latch_bus.py) tests a
parallel alternative: assume both D banks receive the same corresponding
executed Y bits, the 74LS273 clocks after `12A` Y settles but before the
following `127` Y settles, and the 74LS373 output enable prevents both
chips from driving disagreeing Q values. The other four 74LS273 D inputs,
the clock, output enable, DAC08 bus and analog line remain untraced.

The call and answer runs each execute 1,248,256 real-PROM words under the
saved controller-fed fixture. Their trace hashes and the 832 early and late
sample hashes match the previous [clock-order replay](JOINT-MASK04-TX-12A-DELAYED-LATCH.md).
The direct early 74LS273 capture therefore reproduces that replay's
ROM-sensitive `12A` byte stream without assuming an unobserved serial
74LS373→74LS273 data route. Its six candidate DAC bus orders retain zero
filtered A3/A4 data errors in the saved control; the late `127` capture
has 0–1 call and 2–3 answer errors. Every early byte differs from its
late-clock control in these runs.

The visible Q↔Q pairs impose a separate constraint. Immediately before
each proposed 74LS273 clock, that register still holds the previous
sample, while a transparent 74LS373 on the shared D inputs presents the
current Y byte. Their paired upper-four-bit Q values disagree on **831 of
831** checked transitions for both call and answer (1,982 and 1,978 bit
disagreements). If both Q outputs were enabled, these lines would have
opposing digital drivers. A viable parallel model must disable the
74LS373 outputs during that interval or otherwise arbitrate the bus;
after both latches hold the same byte, simultaneous equal logic values
are possible. This is a logic-level prediction, not a current measurement
or proof of the actual output-enable schedule.

The [source-hashed report](results/joint-mask04-tx-parallel-latch-bus.json)
records the sample hashes, bit conflicts and saved line scores. The photo
does not establish the remaining D inputs, 74LS273 clock edge, 74LS373
output enable or DAC08/line route. Next test a pin-compatible enable/clock
schedule against the raw PROM edges and the controller's A1/A3/A4 timing,
or constrain the DAC input from another visible trace. C2 and G2 remain
active under these explicit assumptions.
