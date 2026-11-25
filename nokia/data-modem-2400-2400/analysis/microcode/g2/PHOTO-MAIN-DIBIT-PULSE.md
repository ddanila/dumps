# A counter-qualified dibit pulse can phase-modulate the candidate carrier

The [held-bit experiment](PHOTO-MAIN-FRAME-LINE-HOLD.md) changed D127
throughout each line bit and shifted the carrier frequency. This bounded
[PROM replay](photo_main_dibit_pulse.py) tests a different, explicit hardware
hypothesis: the photographed U1 SN74LS280 parity part and U24 74LS161 counter
could qualify the two real USART-01 bits for only four PC127 visits at each
1,200-symbol/s boundary. Their nets are **not traced**, and neither part is
proved to implement this rule on the Nokia board.

The candidate main-data frame decodes to D127=`B0`. For a dibit with
least-significant bit `b0` and next bit `b1`, the pulse clears D127 D4 when
`b0 XOR b1` is one and clears D5 when `b1` is one; D127 returns to `B0` for
the remaining 2,996 visits of the symbol. At the assumed 14.4 MHz
microinstruction clock, four words per PC127 loop and 9,600 candidate DAC
samples/s, a symbol spans 3,000 loop visits and a four-visit pulse spans 16
microinstructions. Screening pulse widths 1–8 shows that **four** is the only
width in that set giving all four quarter-cycle phase offsets. In 256-step
phase-index units, dibits `00`, `01`, `10`, `11` produce `00`, `C0`, `40`,
`80`: the negative-phase orientation of the [reference model's](reference_modem.py)
`00`, `40`, `C0`, `80` Gray order. The physical phase orientation is unverified.
Here `b0` is the **first serial bit**, and the saved numeric dibit is
`b0 + 2×b1`. V.26 ter instead writes that first bit as the **left** dibit
digit. The [segment-2 standard calibration](PHOTO-SEGMENT2-STANDARD-CALIBRATION.md)
shows that exchanging the two candidate D127 bit lanes is needed for the
surviving DAC buses to decode the controller's A4 pattern with the standard
90°/270° assignments. The original run's internal dibit labels should not
be read as V.26 ter labels.

The unchanged DSC PROMs then run through **every dibit** in each of the four
recorded controller USART streams: 32 dibits in classes `00`/`20` and 24 in
`40`/`60`. The runs execute 384,256 or 288,256 consecutive microinstructions
and verify respectively **96,054 or 72,054** selected PC129 ROM addresses,
bytes and Am2901 Y values against the cumulative phase recurrence. Every
symbol retains its expected phase offset; all four dibit values occur in
the real streams. The seven candidate DAC samples after each pulse keep the
same per-sample phase increment `D0` (208 decimal), the aliased 1,800 Hz
carrier step at 9,600 samples/s. The table shows the first eight symbols for
orientation.

| Controller selector | First eight dibits | Cumulative phase offset after each dibit |
| --- | --- | --- |
| `00` | `2 1 0 0 0 2 3 3` | `40 00 00 00 00 40 C0 40` |
| `20` | `3 1 2 3 3 2 3 1` | `80 40 80 00 80 C0 40 00` |
| `40` | `1 2 3 3 3 1 0 0` | `C0 00 80 00 80 40 40 40` |
| `60` | `0 2 3 3 3 1 0 0` | `00 40 C0 40 C0 80 80 80` |

| Controller selector | Dibits / candidate DAC samples | Candidate full-stream peak | Raised-cosine reference peak | Distinct candidate / reference codes |
| --- | ---: | ---: | ---: | ---: |
| `00` | 32 / 256 | 1,780 Hz | 1,780 Hz | 16 / 99 |
| `20` | 32 / 256 | **2,390 Hz** | **1,560 Hz** | 16 / 104 |
| `40` | 24 / 192 | 1,730 Hz | 1,730 Hz | 16 / 80 |
| `60` | 24 / 192 | 1,720 Hz | 1,720 Hz | 16 / 86 |

The shorter **eight-symbol prefixes** peak at 1,770/1,770, 2,050/2,060,
1,910/1,920 and 2,380/1,920 Hz (candidate/reference). A varying-data
burst cannot be judged by an exact 1,800 Hz peak alone; even the independent
reference moves. The full-stream selector-`20` mismatch is nevertheless a
specific failure of this candidate output route against that reference.
The candidate DAC bus and clock are untraced, and the four-visit rule makes
abrupt phase jumps without a demonstrated pulse-shaping filter. This is a
**conditional four-way phase lead**, not a C2 transmitter pass or a
line-output waveform.

The [machine report](results/photo-main-dibit-pulse.json) records all four
controller dibit sequences, phase checkpoints, first DAC codes, width screen,
full-stream spectra and source hashes. The available board photos show U1
and U24 but do not establish their proposed route. Next vary the candidate
DAC bus, phase orientation and shaping route against the full-stream mismatch,
then test the required segment-1 180° reversals. Keep the receiver and echo
paths open as separate G2 requirements.

The subsequent [full-bus decode screen](PHOTO-MAIN-DIBIT-DAC-DECODE.md)
finds that the existing ordered Y/Q4-Q5-swapped candidate lets an independent
reference receiver recover 103 of 104 real controller dibits. Five other
simple photo-B5-compatible bus orders make at least 31 errors. This strongly
discriminates the *conditional* output byte order but does not trace the
latch clock, prove line output or supply DSC receive processing.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/photo_main_dibit_pulse.py
```
