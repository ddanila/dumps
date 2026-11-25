# No reached state byte shows rapid selective echo attenuation in the fixed fixture

The [first own-echo feed](JOINT-UPPER-ECHO-FEED.md) observed only `Y3F8`.
This [output-site screen](joint_upper_echo_output_screen.py) repeats its
zero-input, remote-only, own-echo and remote-plus-echo controls on the same
joint field map for call (`40`) and answer (`60`). It captures Y at `3F8–3FA`,
Q, and all 16 RAM bytes after every `3FA` visit, then compares the center of
each of 128 held ADC samples. Every run completes 24,000 real-PROM `D3F8`
visits. The new `Y3F8` ratios reproduce the first experiment exactly.

The table shows the remote-plus-echo minus remote-only response, divided by
the injected echo RMS, in the first and last 32-sample windows. A byte is
listed only when its remote-only response exceeds 0.1 times remote input RMS
in **every** window. The [machine report](results/joint-upper-echo-output-screen.json)
contains all 20 bytes, four windows, both selectors, paired trace digests,
and source hashes.

| State byte | Call: first → last | Answer: first → last | Remote-only response range |
| --- | ---: | ---: | ---: |
| `Y3F8` | 1.090 → 1.014 | 1.090 → 1.010 | 1.067–1.117 |
| `Y3F9` | 1.388 → 1.010 | 1.388 → 1.186 | 0.890–1.074 |
| `Y3FA` | 0.508 → 0.503 | 0.508 → 0.492 | 0.522–0.628 |
| `Q` | 0.225 → 0.208 | 0.225 → 0.220 | 0.219–0.263 |
| `R10` | 0.240 → 0.231 | 0.240 → 0.200 | 0.223–0.257 |
| `R11` | 1.090 → 1.014 | 1.090 → 1.010 | 1.067–1.117 |
| `R12` | 1.436 → 1.025 | 1.436 → 1.215 | 0.931–1.108 |
| `R13` | 0.549 → 0.447 | 0.549 → 0.427 | 0.389–0.599 |

None of these remote-responsive bytes halves its mixed-input echo response
between the first and last windows. The smaller ratios at `Y3FA`, Q and
R10/R13 coincide with smaller remote-signal response; they are not by
themselves selective echo cancellation. The other 12 RAM bytes do not meet
the remote-response threshold. A signed modulo-256 byte difference is only
a diagnostic for Q and RAM because their coding and wrap are unknown.

This narrows a **fixed-mode, direct-byte readout** hypothesis. It does not
exclude a longer training interval, an untested latch/output path, or a
controller-qualified mode. The DAC order, analog echo coupling, ADC bus,
clock and train/freeze route are still assumed. C4 remains open. The
[A3→A4 controller edge](CONTROLLER-A3-A4-MODE-EDGE.md) supplies a possible
history-qualified event for a future mode-input test, but is not known to be
the echo-freeze command.

Reproduce with:

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/joint_upper_echo_output_screen.py
```
