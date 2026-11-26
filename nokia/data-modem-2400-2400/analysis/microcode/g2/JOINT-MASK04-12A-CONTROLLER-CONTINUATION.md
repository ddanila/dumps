# Consecutive A4/A5 controller writes survive the joined DSC replay

The [joined A4/data test](JOINT-MASK04-12A-JOINED-A4-DATA.md) used
controller-verified A4 bits followed by payload bytes generated in a
separate controller fixture. Here, all bits come from **one unchanged
8031 ROM execution**: the saved 64-iteration `40` or `60` run writes
eight A4 bytes and then at least nine A5 bytes to line-side port `01`.
Each write was already checked against the controller scrambler. The
V.26 ter segment-2 window begins at bit 1 of the first A4 byte, so the
first 129 consecutive written bits are aligned from that bit and packed
into 16 line bytes. The first eight are the exact known segment-2
pattern; the next eight are held out from phase training.

| Selector | Controller-derived A4 bytes | Following controller-derived A5 bytes | Exact A4-trained maps | Following bytes recovered through DSC |
| --- | --- | --- | ---: | --- |
| `40` | `FC 03 7C 0E 0E F8 C0 18` | `FE 82 75 F5 96 EE A0 70` | 1/64 | 8/8 exact |
| `60` | `FC 03 7C CE 07 E1 84 EC` | `6C 0E 36 91 14 18 8A DA` | 1/64 | 8/8 exact |

For each selector, the real-PROM q3/mask-04 DSC transmitter executes
continuously across all 64 dibits under the same conditional `12A`
DAC/line model. One sustained executed DSC receiver sees the resulting
ADC sequence. The 32 known A4 dibits alone select the same unique
four-state phase labels `2→0, 6→3, 9→1, D→2`; the next 32 dibits make
no errors and reconstruct the eight A5-derived line bytes. This is
stronger than a stitched controller input because the entire 129-bit
source span is from one controller execution.

The 64-iteration 8031 fixture forces timer expiry and holds USART-ready
status high. It records port-`01` **writes**, while the separate paced
8251 model currently proves only the first nine TxD bytes. Therefore
the continuation assumes that the following writes reach TxD in
order, without loss, and that bit-1 framing is used. The R1 phase
intervention, DAC/ADC connections, line filter, clock/capture phases,
external phase map and SYNDET/serial receive route remain hypotheses.
The 16-byte reverse 8251/8031 handoff is not modeled. C2/C3/G2 stay
open; the next concrete test is to extend the paced 8251 TxD model
through at least 17 characters, then feed its actual shifted bits to
the same DSC candidate and test a photo-compatible receive circuit.

The [machine report](results/joint-mask04-12a-controller-continuation.json)
records controller provenance, real-PROM trace digests, line/ADC
hashes, phase-map enumeration and exact held-out bytes. Reproduce from
the microcode directory with:

```sh
python3 g2/joint_mask04_12a_controller_continuation.py
```
