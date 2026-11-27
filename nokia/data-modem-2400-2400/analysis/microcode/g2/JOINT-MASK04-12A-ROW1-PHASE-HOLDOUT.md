# Frozen row-0 Y1 phase-table holdout

The [early-bit graph](JOINT-MASK04-12A-EARLY-BIT-PHASE-GRAPH.md) fit 18 saved
real-PROM receive streams with one extra captured bit: row-0 Y1 at visit `46`.
This experiment froze its 24-code relative phase table before running four
new eight-byte controller payloads at 0.75× receive gain. Transmit and receive
both execute the real PROMs. The controller result is reported only where the
frozen table covers every captured state.

| Carrier start | Controller selector | Unseen eight-bit keys | Wrong transitions between known keys | Result |
| --- | --- | ---: | ---: | --- |
| `141` | `40` | 0 | 0 | Exact dibits, modeled line bytes, and executed controller payload |
| `141` | `60` | 0 | 0 | Exact dibits, modeled line bytes, and executed controller payload |
| `143` | `40` | `05C`, `0E5` | 5 | Frozen table cannot classify stream |
| `143` | `60` | `05C`, `0E5` | 4 | Frozen table cannot classify stream |

The two carrier-`143` streams have no modeled clipping. Their errors between
already known keys independently reject transfer of this one-bit phase table;
the unknown keys were not assigned guessed labels or passed to the modeled
serial/controller path. The old seven-bit veto would also fail these fresh
streams (23/24 dibit errors at `141`, 18/15 at `143`).

An [audit of the saved captures](results/joint-mask04-12a-row1-holdout-graph-audit.json)
joins the 18 prior streams with these four, for 22 streams and 1,430 symbols.
None of the 80 single-bit choices across visits `46`, `47`, `93`, `94`, and
`141` removes all phase-graph conflicts; the minimum is 24. Starting from
either row-0 Y1 or first `3F8` Y4 at visit `46`, adding `3F8` Y4 or Y5 at
visit `94` yields zero conflicts. The row-0 Y1 plus later Y4 graph has one
31-code component. These two-bit choices were selected **using** the new
carrier-`143` failure, so they are development fits and need a fresh frozen
holdout. A conflict-free graph does not establish a gate circuit, captured
physical nets, or the DSC-to-USART connection.

Reproduce the saved-data audit with
`python3 g2/joint_mask04_12a_row1_holdout_graph_audit.py`. The complete
real-PROM captures and frozen-table classifications are in
`results/joint-mask04-12a-row1-phase-holdout-{141,143}.json` and
`results/joint-mask04-12a-row1-phase-holdout.json`. The gain fixture is in
`results/joint-mask04-12a-row1-phase-gain075-fixture.json`.

Next, freeze one two-bit, photo-compatible capture route and challenge new
payload/carrier/gain data. Keep C3 and G2 active; the failed one-bit route and
unknown photographed connections are reasons for the next test, not blockers.
