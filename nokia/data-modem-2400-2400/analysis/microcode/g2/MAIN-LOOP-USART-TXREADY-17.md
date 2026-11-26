# Paced 8251 TxD carries the full controller span used by the DSC replay

The earlier [TxRDY model](MAIN-LOOP-USART-TXREADY.md) verified nine
shifted characters through the A4→A5 boundary. The
[controller-to-DSC continuation](JOINT-MASK04-12A-CONTROLLER-CONTINUATION.md)
uses 129 bits from the first 17 consecutive port-01 writes, so it
still assumed that the later writes reach TxD in order. This replay
extends the unchanged-ROM, Timer-1-paced controller/one-byte-8251
model through 70 A5 polling passes, long enough to shift at least 17
characters. It tests both `40`/`60` selectors at the same eight
one-bit-spaced Tx clock phases as the earlier model.

| Selector | First 17 actual modeled TxD characters | Sampled clock phases with exact match to controller writes and DSC input |
| --- | --- | ---: |
| `40` | `F9 07 F8 1C 1C F0 81 31 FC 05 EB EA 2D DD 41 E1 EA` | 8/8 |
| `60` | `F8 07 F8 9C 0F C2 09 D9 D9 1C 6C 22 29 30 14 B5 AD` | 8/8 |

All 16 controller runs stay in A1→A2→A3→A4→A5, report zero
emulator/buffer errors, and shift at least 17 complete data characters.
The first 17 TxD bytes equal the first 17 writes from the independent
64-iteration controller run, despite TxRDY changing the number of
polling passes per state. Repacking TxD bits 1–128 into 16 bytes
exactly reproduces the source bytes fed to the earlier joined
real-PROM DSC Tx→line→Rx replays in **every sampled phase**. The
write-versus-shift gap in that conditional chain is therefore closed
for this modeled 8251, bit clock and set of phases.

The 8251 model assumes a one-byte buffer, 2400-bit/s clock, initial
`FF` sync fill and CTS permission. The controller still needs a
RAM15-positive gate plus synthetic receive/status input. The physical
TxD-to-DSC connection, first-data-bit alignment, DAC/ADC/line route,
receiver phase decision and reverse serial handoff remain untraced.
C2/C3/G2 stay active. Next feed the paced bit events and their timing
directly into a photo-compatible DSC serial input circuit, then test
the reverse 8251/8031 handoff without using payload labels.

The [machine report](results/main-loop-usart-txready-17.json) records
all 16 controller runs, shifted bytes, timing and source hashes.
Reproduce from the microcode directory with:

```sh
python3 g2/main_loop_usart_txready_17.py
```
