# Controller-derived bits move the second ROM address but do not reach output in this fixture

The [PC12C recurrence](PHOTO-12C-PHASE-SCAN.md) invites a changing-input
test. The [stream runner](photo_12c_controller_stream.py) executes the
unchanged 8031 ROM's scrambler to obtain 16 bytes (128 bits, 57 ones), then
offers those bits to the hypothetical DSC2847 PC12C D input after held
D127=`81` enters the second loop. It tests forward order and a diagnostic
reverse order, holding each bit for 1, 2, 4 or 8 PC12C visits. An explicit
idle `0` follows the 128 bits. These bit order, timing and connection
choices are scenario hypotheses, not observed board wiring.

Each case executes 4,000 real-PROM microinstructions. The runner verifies
every offered PC12C bit and selected Am27S31 address against
`0x100 + ((1 + cumulative input sum) mod 256)`.

| Visits per bit | Forward PC12C visits / outcome | Reverse diagnostic visits / outcome |
| ---: | --- | --- |
| 1 | 864; all 128 positions consumed, then idle; stays in loop | same |
| 2 | 864; all 128 positions consumed, then idle; stays in loop | same |
| 4 | 864; all 128 positions consumed, then idle; stays in loop | same |
| 8 | 615; reaches zero after 77 bit positions, then PC084 | 479; reaches zero after 60 positions, then PC084 |

For the 1/2/4-visit schedules, the cumulative advance is 57/114/228,
respectively, so the phase never reaches zero. Eight-visit holds reach 255
ones before all 128 bit positions are presented. Neither outcome is a
sustained 128-bit transmit run: every case has **zero visits** to candidate
output words `392` and `39E`.

A paired PC12E-bank run for every schedule changes most selected ROM bytes,
but preserves the PC sequence and every modeled RAM/Q/flag/stack/next-PC
checkpoint after PC12D. This extends the
[constant-input liveness result](PHOTO-12C-BANK-LIVENESS.md) to changing
controller-derived input: the ROM operand is transient under this mapping
and timing. An external latch could still sample it; the latch clock and
DAC data path remain untraced. The
[machine report](results/photo-12c-controller-stream.json) includes the
controller bytes, per-case input and ROM counts, bank differences, wait
timing, trace digests and source hashes.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/photo_12c_controller_stream.py
```
