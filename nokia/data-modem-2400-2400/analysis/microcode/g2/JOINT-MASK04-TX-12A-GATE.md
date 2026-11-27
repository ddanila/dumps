# A two-bit PROM decode can clock the settled `12A` transmitter byte

The [bank-edge timing result](JOINT-MASK04-TX-BANK-EDGE-TIMING.md) showed
that the proposed U10 D2 edge arrives before the bank-sensitive `12A` Y
byte is available. This [new gate screen](joint_mask04_tx_12a_gate.py)
finds a later, photo-compatible clock hypothesis in the same four real
control PROMs: `U11.D0 & U17.D1` is high at `12A` and low when the loop
fetches the next `127`. A NAND of these two PROM outputs would therefore
have a rising edge at `12A→127`. If the PROM gate changes before the
new `127` ALU result propagates to Y, a latch on that edge captures the
preceding, settled `12A` Y byte. The relative propagation timing and
gate-to-latch net remain assumptions.

Among the 39 PCs reached in a 4,096-instruction held-tone run, no
single PROM literal identifies `12A`; this is the sole two-literal
conjunction that does. The gate is high on all 1,014 `12A` visits and
has 1,013 observed `12A→127` falling-level transitions; the last visit
is the final trace word. In a paired run changing only the selected
Am27S31 bank at `129`, the Y byte available at those transitions differs
on 221 edges, always by bit 0. Thus this clock/data ordering would carry
the ROM-bank effect that the earlier direct U10 D2 clock misses.

The call (`40`) and answer (`60`) controller-fed runs each execute
1,248,256 real-PROM words and reach the same 39 PCs. In both, this gate
is high **only** at `12A`, on all 312,054 visits. Their trace digests
match the upper-bank runs in the [full bank-phase replay](JOINT-MASK04-TX-BANK-PHASE.md),
which already measured bank-dependent settled `12A` Y values on 75,012
and 75,018 visits, respectively. A counter selecting every 375th
candidate edge is still an assumed 9,600-sample/s clock.

The two-bit conjunction also selects 110 other words in the entire
1,024-word store; its exclusivity is measured only for these executed
transmitter modes. Neither the PROM-to-gate wiring, latch clock/data
pins, setup/hold timing, DAC bus, nor analog line output is established
from the photos. This supplies a runnable post-`12A` C2 route rather
than a C2 pass. The next test is to execute a counter-qualified NAND
edge with realistic relative gate/Y delays across the full stream and
compare the resulting DAC codes with the six surviving bus orders.

The [machine report](results/joint-mask04-tx-12a-gate.json) contains
gate definitions, reached-PC counts, paired bank contrasts, trace
digests and source hashes. Reproduce with
`python3 g2/joint_mask04_tx_12a_gate.py`.

The later [whole-store audit](JOINT-MASK04-TX-12A-FULL-STORE-GATE.md)
finds that this two-bit level also selects receive-address words. A
four-literal product uniquely selects `12A` in the entire PROM store;
the shorter three-literal extension removes all `3E0–3FF` aliases. These
are alternative, still-untraced clock decodes for the direct 74LS273
candidate.
