# Direct upper-ROM byte fails the fast-gated tone test

The [runner](photo_127_full_byte_gate.py) tests a different data route from
the [PC129 phase loop](PHOTO-127-LIVENESS.md): latch the selected upper-bank
Am27S31 **byte**, rather than its transient ALU Y. The ROM-to-74LS273 route,
clock and DAC bit order are hypotheses. Four D127 values from the
[fast-clock screen](PHOTO-127-FAST-STEP-CANDIDATES.md) are executed for 740
PC129 reads each. Every selected address, ROM byte and Y value matches the
loop recurrence. The 64-sample, 9,600 Hz latch series are then projected
from that checked recurrence at 375 or 125 loop visits per sample, including
all 16 or 32 reachable visit alignments. Thus the spectra extend beyond the
executed 740-read trace and are **conditional projections**.

| Assumed DAC byte | 1,800 Hz case: peak / target R² | 2,100 Hz case: peak / target R² |
| --- | ---: | ---: |
| Selected ROM byte, raw | 3,000 Hz / 0.051 | 3,000 Hz / 0.155 |
| Selected ROM byte with B8 inverted | 1,800 Hz / 0.431 | 2,100 Hz / 0.442 |
| PC129 ALU Y | 1,800 Hz / 0.626 | 2,100 Hz / 0.346 |
| Phase-index ramp control | 1,800 Hz / 0.618 | 2,100 Hz / 0.610 |

The `k=1` and `k=3` clock/divisor pairs give identical sampled phase steps
and spectra. The raw-ROM byte is not a viable direct DAC code for both
target tones in this fixture. Inverting its high bit yields both peak bins,
but no high-bit inversion is traced and the target sinusoids explain under
half the code variance. ALU Y's 1,800 Hz score barely exceeds the phase
ramp, so its peak is weak evidence of a carrier. The upper ROM bank begins
with a quarter-sine table but contains other data after it; a full 256-step
index sweep is not a full sine lookup.

The [machine report](results/photo-127-full-byte-gate.json) contains the
four executed-trace digests and every candidate spectrum. This narrows
simple direct-byte routes, while a decoded quarter-wave lookup, different
ROM-bank/address path, staged latch, or controller-selected step remains
testable. It does not establish command-driven modulation, DAC08 pins or
the physical line output.
