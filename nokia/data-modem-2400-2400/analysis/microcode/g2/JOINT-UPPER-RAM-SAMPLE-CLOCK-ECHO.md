# Sample-paced RAM feedback sustains reception but does not attenuate the tested Y proxy

The [training/freeze screen](JOINT-UPPER-RAM-FREEZE-SCREEN.md) used a
counter tick on every receive-loop visit. This [PROM replay](joint_upper_ram_sample_clock_echo.py)
instead advances the assumed RAM address once per held ADC sample:
alternating 188 and 187 loop visits per sample. It writes the low nibble
of `3FA` Y to a candidate 256×8 RAM bank at `3EC`, freezes after 128
training samples, and reads a previous address's low nibble back into
`3FA` D. Two read offsets, three and 64 samples, represent distinct
untraced address-mux possibilities. The no-feedback control still trains
and freezes the RAM.

The 128-sample training inputs are zero, an independent remote DPSK
stream, and candidate own echoes from each of the controller's `40`
and `60` transmit streams. The latter use the existing hash-checked
real-PROM DAC-code candidates, with an assumed three-sample delay and
half gain. All inputs then receive the same 64 zero-amplitude samples.
Every one of the 12 runs completes 36,000 ADC visits without a loop
exit, and every RAM writes exactly 24,000 times before freezing.

The RAM return changes executed `3FA` Y during the common tail, but
does not change `3F8` or `3F9` Y relative to each same-input
no-feedback control. The number of changed `3FA` tail visits is:

| Training input | Three-sample read | 64-sample read |
| --- | ---: | ---: |
| Zero | 563 | 12,000 |
| Independent remote | 563 | 11,251 |
| Own echo, selector `40` | 563 | 8,626 |
| Own echo, selector `60` | 375 | 8,626 |

This response is not selective to own echo; zero and remote training
also change the same output site. As a diagnostic code-space measure,
the mean absolute `3FA` Y difference between each input and the
same-route zero run during training is:

| Input | No feedback | Three-sample read | 64-sample read |
| --- | ---: | ---: | ---: |
| Independent remote | 6.865 | 9.233 | 7.646 |
| Own echo, `40` | 6.225 | 8.074 | 7.020 |
| Own echo, `60` | 6.259 | 8.162 | 7.040 |

Neither tested RAM offset reduces this proxy response to own echo.
The result constrains this particular sample-clocked, `3FA`-return,
freezing fixture; it is **not** an analog line-residual measurement.
The RAM address clock, read offset, write gate, D0 forcing, DAC/ADC
routes and output latch remain assumptions. C4 stays open. The next
useful test is a different photo-compatible return/output or mode
route, with a line-output candidate and an own-echo-versus-remote
residual control. Missing continuity data does not block that test.

The [machine report](results/joint-upper-ram-sample-clock-echo.json)
contains input and trace hashes, RAM hashes, first changed reads,
per-site tail differences and code-space responses. Reproduce from
the microcode directory with
`python3 g2/joint_upper_ram_sample_clock_echo.py`.
