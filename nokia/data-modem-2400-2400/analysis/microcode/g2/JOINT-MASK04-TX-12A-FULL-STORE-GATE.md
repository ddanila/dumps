# A whole-store `12A` decode sharpens the direct 74LS273 clock hypothesis

The earlier two-bit raw-PROM conjunction `U11.D0 & U17.D1` is high only at
`12A` among the 39 addresses reached in the executed call/answer
transmitter loop. It is high at **111** of the full store's 1,024 words,
however, including `3E1`, `3E5`, `3E9`, `3F2`, `3F6`, `3FA`, `3FE` and
`3FF` in the receive-address span. A free-running use of that two-bit
level as a DAC clock would need additional qualification outside the
tested transmit loop.

The [full-store gate audit](results/joint-mask04-tx-12a-full-store-gate.json)
exhaustively tests conjunctions of the 32 raw-PROM output literals with
the polarity present at `12A`. Adding `U18.D1=0` to the old two literals
reduces the whole-store hits to 15 and eliminates **every** hit in
`3E0–3FF`; `12A` remains the only hit in `120–140`. Adding `U17.D3=1`
isolates `12A` across all 1,024 words:

`U11.D0 & U17.D1 & U17.D3 & ~U18.D1`.

No one-, two- or three-literal conjunction uniquely selects `12A` in
the full store. The audit finds exactly two four-literal minimum products;
the other replaces `U17.D1` with `~U17.D2`. An all-positive decode
cannot isolate `12A` even with every one of its eleven high raw-PROM
bits: `12F`, `1DF`, `29F` and `3FF` remain aliases. Thus an inverted
input or equivalent logic is required for this direct whole-store
product. This is a Boolean capacity result, **not** evidence that the
board wires those PROM outputs together.

The four-literal level is high at `12A` and low at the following `127`,
so an inverted clock could still rise on `12A→127`. To capture the
preceding settled Y directly in the 74LS273, the [TI 74LS273 datasheet](https://www.ti.com/lit/ds/symlink/sn74ls273.pdf)
requires at least 20 ns of data setup and 5 ns of hold around that rising
edge. In event-time terms, the assumed circuit needs
`t(12A Y valid) ≤ t(clock) − 20 ns` and
`t(127 Y changes) ≥ t(clock) + 5 ns`. The PROM, gate, counter, Am2901 and
board-route propagation delays have not been measured, so the inequalities
are **requirements**, not a demonstrated margin.

The [latch pin audit](PHOTO-DED-LATCH-BUS.md#pin-function-audit-of-the-visible-tracks)
weakens the simple serial 74LS373→74LS273 hold explanation. A direct
early-edge 74LS273 capture therefore deserves a separate circuit test:
trace or bound the clock/data path, preserve the `12A` bank-sensitive
sample hash, and compare the late-edge control. The whole-store decode
reduces mode aliases but does not identify the actual net. Keep C2 and
G2 active.
