# The candidate A4 sync frame is written before line data

The [A3→A4 frame probe](CONTROLLER-A3-A4-MODE-EDGE.md) found one exact
third-frame-byte `81→A1` transition at A4 entry. The controller's first A4
line-data byte is also written near this boundary. To test their order, this
[instruction-level probe](controller_syndet_edge_timing.py) instruments the
unchanged 8031 ROM run and records each SBUF write to the four-byte CD4094
frame and the first MOVX write to line-side USART port 01. It uses the same
Timer 1 fixture, held-positive RAM15 gate and synthetic peripheral events as
the [interrupt-paced run](MAIN-LOOP-TIMER1-SEGMENT2.md).

| Selector | First A4 SBUF frame write cycles (`D0 42 A1 BA`) | First port-01 data write | Lead from final SBUF write |
| --- | --- | --- | --- |
| `40` call | 2,702,911; 2,702,924; 2,702,937; 2,702,950 | `F9` at 2,703,100 | 150 emulator ticks |
| `60` answer | 2,703,240; 2,703,253; 2,703,266; 2,703,279 | `F8` at 2,703,403 | 124 emulator ticks |

The third frame byte is written 163 and 137 ticks before the first data
write, respectively. The result makes an **external decoder of the exact
`81→A1` transition** a runnable SYNDET hypothesis: under this controller
fixture, its input frame is emitted before the controller supplies the first
data byte. The [external-SYNDET receive test](RECEIVER-MASK04-EXTERNAL-SYNC-HANDOFF.md)
shows what would happen *if* that decoder produced a pulse immediately before
the first data RxC edge. A plain rise of third-byte bit 5 is not a sufficient
decoder because it also occurs earlier in the operating sequence.

This is a firmware event-order constraint, not a measured SYNDET timing
margin. The probe asserts serial completion eight emulator ticks after each
SBUF write; it does not model the physical CD4094 shift and latch, decoder
delay, RxC phase, or the connection from the frame logic to the 8251A's
SYNDET pin. The port-01 write is **local transmit data**; its time cannot
locate the first arriving remote bit. Those remain labelled assumptions.
C3 is open. The next test
should vary physical frame-delivery and RxC phase hypotheses against the
first-data-bit, early and late pulse controls, or find an independent
photo-compatible SYNDET source.

The [machine report](results/controller-syndet-edge-timing.json) records the
event PCs, cycles, fixture and source hashes. Reproduce from the microcode
directory with `python3 g2/controller_syndet_edge_timing.py`.
