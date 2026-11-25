# The D127 ROM operand is transient in the held-I0 loop

The [paired execution](photo_127_liveness.py) changes only the Am27S31 A8
bank selected at `PC129`; other ROM reads stay in the upper bank. Both runs
use the real PROMs, the `q3` photo-swapped mapping, Q=0, zero initial RAM,
the hypothetical held-I0 level and a constant D127 input. These are scenario
assumptions, not recovered Nokia wiring.

For each repeated `127 → 128 → 129 → 12A` quartet, the model verifies:

- `phase = (3 + n × D127) mod 256`, written to R1 at `127`;
- `Y129 = (phase − ROM[bank + phase]) mod 256`;
- `carry129 = 1` when `phase ≥ ROM[bank + phase]`;
- `Y12A = (phase + 1 + carry129) mod 256`.

R0 writes at `128`, `129` and `12A` are conditional in the model. The ROM
value can therefore change `Y129` and the following carry-dependent `Y12A`,
but those values are not automatically a retained sample stream. A snapshot
after each `PC128` includes all modeled RAM, Q, ALU flags, next PC and stack.
The two banks give identical snapshots at every paired checkpoint:

| D127 | PC129 reads | Different ROM bytes / Y129 | Different Y12A | Different PC128 snapshots |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 253 | 249 | 69 | 0 / 253 |
| 48 | 740 | 694 | 233 | 0 / 740 |
| 56 | 740 | 717 | 232 | 0 / 740 |

This rules out a **retained** bank effect in this specific fixture. It does
not rule out a physical latch sampling the transient byte or carry at `129`
or `12A`. The latch clock and DAC data path have not been traced, and neither
bank produces a verified line-output waveform. A useful next test must put
a photo-compatible sampling phase on these transient sites, or find a
different ROM path whose effects persist into later controller-driven work.
The [raw PROM edge screen](PHOTO-127-CLOCK-SCREEN.md) finds direct bit edges
at every visit, but their unqualified rate is too high for the proposed
9,600 Hz sample cadence under the fast-clock hypothesis.

The [result](results/photo-127-liveness.json) contains trace digests, source
hashes and the checked counts. Reproduce it with:

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/photo_127_liveness.py
```
