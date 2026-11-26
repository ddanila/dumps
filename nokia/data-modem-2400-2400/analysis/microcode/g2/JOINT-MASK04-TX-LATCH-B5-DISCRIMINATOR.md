# The visible-candidate DAC08 B5 bit sharply separates two latch topologies

The [B5 replay](joint_mask04_tx_latch_b5_discriminator.py) reruns the
upper-bank, controller-fed call and answer transmitter streams for
1,248,256 real-PROM words each. Their trace and both candidate sample
hashes match the prior [timed-latch execution](JOINT-MASK04-TX-12A-DELAYED-LATCH.md).
It compares two explicit circuits at the same 832 sample clocks:

- **Serial hold:** the assumed 74LS373 retains settled `12A` Y while the
  74LS273 clocks later at `127→128`.
- **Shared Y input:** 74LS273 D sees live Y and the same later clock captures
  settled `127` Y; the 74LS373 may have another bus role.

All six surviving photo-compatible DAC orders map **Y4 to code bit 3**, the
eight-count DAC08 **B5** input. The [front photo](DAC08-OUTPUT.md) suggests
a 74LS273 Q4→DAC08 B5 pin-9 trace. The required Y4→74LS273 D4 input
wire and both clock topologies are **untraced**; the result is a testable
digital pin prediction, not a measured Nokia pin waveform.

| Selector | B5 samples that differ / 832 | A1 tone | A2 silence interval | A3 reversals | A4 data |
| --- | ---: | ---: | ---: | ---: | ---: |
| Call `40` | **698** | 128/256 | 64/64 | 256/256 | 250/256 |
| Answer `60` | **696** | 128/256 | 64/64 | 256/256 | 248/256 |

The prior Q=1 filtered data control makes zero errors on every bus for the
held `12A` samples. With the late shared-Y samples it makes 0–1 call and
2–3 answer errors, depending on bus. These are diagnostic model scores,
not a measurement of the physical analog line. The A2 line stage was
externally muted in that fixture, so its 64 B5 pin differences need not
appear on the line.

The [ROM-bank intervention](JOINT-MASK04-TX-12A-TWO-STAGE-LATCH.md) alone
does **not** use the visible B5 segment to distinguish the topologies:
it changes only `12A` Y0, which every surviving bus maps to DAC code bit
4, the 16-count **B4** input. The normal controller stream instead
predicts many B5 differences even without changing a ROM bank. An
independent observation at DAC08 B5 pin 9, or a reliable trace of the
74LS273 D4/clock route, could choose between these circuits. Until then,
both remain photo-compatible assumptions and C2/G2 stay active.

The [machine report](results/joint-mask04-tx-latch-b5-discriminator.json)
contains the per-segment counts, first differing sample indices, hashes,
prior data scores and source hashes. Reproduce from the microcode directory:

```sh
python3 g2/joint_mask04_tx_latch_b5_discriminator.py
```
