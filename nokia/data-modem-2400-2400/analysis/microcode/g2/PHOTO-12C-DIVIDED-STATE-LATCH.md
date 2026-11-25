# A divided A1 `12E` strobe does not turn the held frame bytes into 2,100 Hz

The [divided-strobe replay](photo_12c_divided_state_latch.py) tests the
output hypothesis left by the [A0/A1 raw-edge screen](PHOTO-12C-PROM-EDGE-LATCH.md):
U18 D1 rises at each A1 `12E` visit, and a hypothetical divider selects
9,600 of those events per second for a 74LS273 capture. Logical CD4094
chip 1 Q8→D0 supplies A1 D127=`81`; one of the other chips supplies held
D12C=`7A`, `02` or `80`. Both `12E` Y and a one-word-delayed `12F` Y are
tested as latch data; Y7→74LS273 D4→Q4→DAC08 B5 is a separate bit-route
hypothesis. The frame-to-DSP, clock, divider and full DAC bus are untraced.

Each held byte is executed for 3,000 real-PROM microinstructions. All 613
selected `12E` ROM values and following `12F` ALU bytes match the phase/ROM/Y
recurrence used to project 640 gated samples. At one or three oscillator
periods per microinstruction, the divider selects every 375th or 125th
`12E` event. Every possible start phase within the held byte's ROM-walk
period gives a circular shift of the same sample sequence, so the spectral
peaks below do not depend on divider alignment:

| Held D12C | Microinstruction divisor | Sampled phase step | `12E` full Y and B5 peak | `12F` full Y and B5 peak |
| ---: | ---: | ---: | ---: | ---: |
| `7A` | 1 | `B6` | 2,775 Hz | 2,775 Hz |
| `7A` | 3 | `92` | 4,125 Hz | 4,125 Hz |
| `02` | 1 | `EE` | 675 Hz | 675 Hz |
| `02` | 3 | `FA` | 225 Hz | 225 Hz |
| `80` | 1 or 3 | `80` | 4,800 Hz | 4,800 Hz |

None peaks at the candidate **2,100 Hz A1 tone**. The target-bin variance
fraction for full `12E` Y is at most 0.009812, and for the photo-supported
B5 candidate at most 0.003478. The spectral calculation includes the
4,800 Hz Nyquist bin, which matters for `80`'s alternating sample series.
The [extended replay](photo_12c_divided_state_latch.py) also covers two and
four oscillator periods per microinstruction. These give fractional
`12E`-visits-per-sample ratios of `375/2` and `375/4`. For each byte and
ratio, it checks every oscillator/sample phase and every offset within the
ROM-walk period, at both `12E` and `12F` and for full Y and candidate B5.
The largest 2,100 Hz variance fraction over all these cases is **0.001283**
(`7A`, divisor 2, `12E` full Y). There are 320 non-DC bins in the 640-sample
real spectrum; their one-sided variance fractions sum to one. Thus a bin
below `1/320 = 0.003125` cannot be the largest. All fractional-site/data
checks fall below that bound, so none has 2,100 Hz as its strongest bin.
The [machine report](results/photo-12c-divided-state-latch.json) records
all twelve divisor/byte cases, the alignment counts, target fractions and
execution digests.

This excludes a **direct, held alternate-chip byte** producing the proposed
A1 tone through this q3 second-loop latch at 9,600 samples/s and the tested
oscillator divisors 1–4.
It does not establish that A1 is the tone state or that this is the physical
DAC route. A decoded/changing D12C phase step, another clock relation or a
different output consumer remains testable; the unknown connections do not
block those experiments.
