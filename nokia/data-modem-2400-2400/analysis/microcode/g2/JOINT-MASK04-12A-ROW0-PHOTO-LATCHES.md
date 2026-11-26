# Photo-compatible three-latch receive candidate

The [replay](joint_mask04_12a_row0_photo_latches.py) assigns the seven bits of
the frozen [22-state phase gate](JOINT-MASK04-12A-ROW0-TWENTYTWO-HOLDOUT.md)
to storage devices identified in the DSC2847 [photo inventory](../board/inventory.json).
This is a **candidate connection**, not a traced Nokia circuit:

| Assumed stage | Value captured | Assumed time within each symbol |
| --- | --- | ---: |
| U12 SN74LS175N, one of four FFs | `3ED` row-0 Y0 | visit 46, cycle 1,522 |
| U14 SN74LS75N, three of four latches | first `3F8` Y5–Y7 | visit 46, cycle 1,535 |
| U3 74LS373 PC, three of eight latches | second `3F8` Y7,Y4,Y6 | visit 93, cycle 3,039 |

The U12 output supplies state bit 6; U14 supplies bits 0–2; U3 supplies
bits 3–5. The two frozen phase outputs have three and two product terms,
respectively. A possible U25 HD74LS74AP pair holds the preceding two-bit
phase for subtraction modulo four; a possible U24 counter qualifies the
row/visit capture, and a possible U28 counter selects the two serial bits.
Those functions, their glue gates, actual pins and board use are all
**unverified assumptions**. The model also assumes an RxC edge at cycle
6,000 and every 6,000 cycles thereafter, plus aligned external SYNDET at
bit 66. Its first reversal dibit comes from the known preamble fixture.

The replay uses 65-symbol snapshots from eight earlier **real-PROM**
transmit→line→receive runs: six call/answer × three line levels at R1 offset
88, and two call/answer payloads at offset 112. It stores each bit in its
candidate stage, checks that staged states agree with the existing event
replay, applies the frozen gates and phase difference, and sends the
serial bits through the modeled external-sync 8251 and executed 8031
receiver probe. It does not re-run the PROM or establish physical wiring.

| Capture/clock alternative | Decision errors across eight runs | Result |
| --- | ---: | --- |
| Three stages as above; RxC at 6,000/12,000 | 0 in every run | Exact eight offered line bytes and eight decoded controller bytes; minimum setup 2,961 cycles |
| U12 row-0 capture one visit later | 0 in every run | Row bit remains stable; this edge is not distinguished |
| U12 takes row 3 instead | 14–25 per run | Rejected for these streams |
| U14 first Y capture one visit later | 6–19 per run | Rejected for these streams |
| U3 second Y capture one visit later | 7–16 per run | Rejected for these streams |
| First RxC at cycle 3,000 | 64 unavailable data-bearing edges per run | Too early for the second Y capture |

This closes the specific **U12-only storage-capacity objection** to a
seven-bit external phase readout: photographed parts could hold all seven
bits if the assumed connections and enables exist. It does not show that
those parts are free, wired that way, or drive USART-01 RxD/RxC/SYNDET.
C3 remains open and G2 active. Next use the same capture/clock controls
on a new real-PROM payload with all four `3ED` row values saved, and test
whether a raw every-row clock can be qualified into this row-0 capture.
Physical continuity can then discriminate surviving routes; it is not a
prerequisite for the next experiment.

The [machine report](results/joint-mask04-12a-row0-photo-latches.json)
contains each run's state count, errors, unavailable edges, bytes, timing
and source hashes. Reproduce from the microcode directory with:

```sh
python3 g2/joint_mask04_12a_row0_photo_latches.py
```
