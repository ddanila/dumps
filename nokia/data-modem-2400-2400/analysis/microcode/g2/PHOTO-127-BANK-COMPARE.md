# Fixed A8 bank selection does not turn the D127 walk into a sine lookup

The [D127-driven ROM walk](PHOTO-I0-HOLD.md) advances the PC129 address low
byte by the offered D127 value under a held-I0, Q=0 mapping hypothesis. The
[two-bank execution](photo_127_bank_compare.py) tests A8 fixed low and high,
with D127 held at 3, 48 or 56. At every executed PC129 visit the address is
`bank + ((3 + n × D127) mod 256)` and ALU Y is the low address byte minus the
selected ROM byte, modulo 256. The run verifies both relations against the
real control PROMs and Am27S31 dump.

| Bank / increment | Selected reads | Hits in sine-table region, analysis window | Signed ROM peak | Signed ALU-Y peak |
| --- | ---: | ---: | ---: | ---: |
| Lower / 3 | 255 | 14/240 in `000–00F` | 1920 Hz | 120 Hz |
| Lower / 48 | 740 | 40/640 in `000–00F` | 2400 Hz | 4200 Hz |
| Lower / 56 | 740 | 40/640 in `000–00F` | 2700 Hz | 2100 Hz |
| Upper / 3 | 255 | 63/240 in `100–140` | 120 Hz | 120 Hz |
| Upper / 48 | 740 | 160/640 in `100–140` | 1800 Hz | 1800 Hz |
| Upper / 56 | 740 | 160/640 in `100–140` | 2100 Hz | 2100 Hz |

Frequencies use an **assumed** 9600 PC129 visits/s. D127=3 in the lower
bank starts with sine-table addresses `006,009,00C,00F`, then reads `012`
and continues across the 256-byte bank. Fixed A8 alone does not wrap the
address at 16, so it is not the 16-sample 1800 Hz sine lookup suggested by
those first four reads. The upper bank similarly spans its quarter-sine
region and other table regions.

Interpreting the ROM bytes as signed changes an earlier spectral observation:
the upper-bank sequences for increments 48 and 56 *do* peak at the respective
1800 and 2100 Hz bins, with sinusoidal variance fractions 0.431 and 0.442.
The earlier [tone probe](PHOTO-I0-HOLD.md#fixed-increment-tone-check)
treated raw bytes as unsigned and reported 3000 Hz peaks. Neither coding is
established at the photographed DAC. More decisively, a ROM-only control
screen projects increments 16, 24, 32, 40, 48, 56, 64, 72 and 80 through the
same executed address rule: **every upper-bank signed sequence peaks at its
chosen phase-step frequency**. The 1800/2100 peaks therefore do not
independently identify a Nokia carrier selection. The selected ROM byte is
an input operand, not a traced DAC sample; ALU Y also includes the phase-index
ramp.

The [report](results/photo-127-bank-compare.json) saves first addresses and
bytes, table-hit counts, signed spectra, trace digests and source hashes.
The next useful constraint is how the physical ROM address pins select or
fold the quarter-sine region, and where a resulting sample would be latched.
Those are assumptions to test, not blockers.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/photo_127_bank_compare.py
```
