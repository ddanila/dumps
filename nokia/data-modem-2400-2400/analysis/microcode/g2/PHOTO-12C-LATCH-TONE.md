# A PC12F latch could carry a tone-rate B5 bit, but its full Y byte remains a ramp

The [second-loop recurrence](PHOTO-12C-PHASE-SCAN.md) exposes transient
ALU values at PC12E and PC12F. The [latch-site screen](photo_12c_latch_tone.py)
tests both as candidates for the photographed DAC08 B5←74LS273 Q4 segment.
It assumes Y7 drives the latch's D4, a latch edge at the chosen word, a
9,600 Hz output gate and one or three 14.4 MHz oscillator periods per
microinstruction. The Y→D4 route, clock, divider and full DAC bus are
untraced.

With D127=`81` to enter the second loop, eight held **even** D12C bytes
from the [fast-step equation](PHOTO-127-FAST-STEP-CANDIDATES.md) each execute
613 selected PC12E reads and 613 following PC12F words. The runner checks
their phase, ROM byte, carry and ALU-Y recurrence, then projects 640 gated
samples under the stated timing assumptions. The forward cases are:

| D12C / divisor | Target | PC12E B5 target R² | PC12F B5 target R² | Phase ramp / PC12F full-Y target R² |
| --- | ---: | ---: | ---: | ---: |
| `50` / 1 | 1,800 Hz | 0.661 | 0.821 | 0.618 / 0.617 |
| `88` / 1 | 2,100 Hz | 0.486 | 0.813 | 0.610 / 0.609 |
| `F0` / 3 | 1,800 Hz | 0.661 | 0.821 | 0.618 / 0.617 |
| `98` / 3 | 2,100 Hz | 0.486 | 0.813 | 0.610 / 0.609 |

The reverse-step partners `B0`, `78`, `10` and `68` give the same frequency
and variance fractions. At PC12F, B5 carries a strong component at the
**chosen phase rate**, but the full Y byte fits no better than the plain
phase-index sawtooth. At PC12E, the full-Y target fraction is 0.609 for
1,800 Hz and 0.348 for 2,100 Hz. The B5 result is therefore a candidate
binary timing signal, **not evidence of a sinusoidal DAC code or carrier**.
The [machine report](results/photo-12c-latch-tone.json) includes all eight
executed cases, projected spectra, trace digests and source/photo hashes.

No controller command is shown to load these D12C bytes. The proposed
clock must also divide or qualify the much faster four-word loop before
the 74LS273 could update at 9,600 samples/s. A full transmitter test still
needs a photo-compatible byte route to the DAC08, a plausible latch clock,
controller-selected tone/data modes and a line waveform. The present
comparison prevents promoting a single B5 spectral peak to that result.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/photo_12c_latch_tone.py
```
