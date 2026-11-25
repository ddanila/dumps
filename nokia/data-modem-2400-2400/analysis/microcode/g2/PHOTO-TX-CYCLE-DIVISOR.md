# The joined transmit fixture favors one microinstruction per oscillator tick

The [divided PROM-clock replay](PHOTO-TX-DIVIDED-PROM-CLOCK.md) assumed that
the DSC runs one microinstruction per 14.4 MHz oscillator tick. This screen
repeats its controller-selector `40` A1 tone → A2 interval → A3 reversals →
A4 data execution with candidate microinstruction rates `14.4 MHz / k`,
`k=1…4`. Each case runs the real four-PROM trace. The assumed D127 tone
step, four-visit dibit pulse, Q3 mapping, preceding-`129` Y latch and six
surviving photo-compatible DAC bus orders are held fixed. The D127 hold per
symbol scales from 3,000 loop visits at `k=1` to 750 at `k=4`, preserving
the hypothetical 1,200-baud input schedule.

At a 9,600 Hz sample rate the budget is `1,500/k` microinstructions per
sample and `12,000/k` per symbol. The recurring four-word loop therefore
supplies `375/k` U10 D2 falling edges per sample. A counter-qualified clock
selects the nearest edge to each ideal sample; `k=2` alternates 187/188
edge gaps and `k=4` alternates 93/94. All four runs complete cleanly and
capture 832 candidate samples. The `k=1` full-state trace digest and DAC
sample hash match the prior independent replay.

| `k` | Microinstruction rate | Edge gaps per sample | Late A1 raw-code peak | Filtered A3/A4 dibit errors |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 14.4 MHz | 375 | 2,100 Hz | 0/63, all six buses |
| 2 | 7.2 MHz | 187/188 | 1,050 Hz | 33–37/63 |
| 3 | 4.8 MHz | 125 | 1,800 Hz | 21/63 |
| 4 | 3.6 MHz | 93/94 | 1,350 Hz | 43–45/63 |

The 1,800 Hz peak at `k=3` is the dominant spectral component of the *raw
candidate code* under this altered clock; it does not restore the expected
A1 2,100 Hz tone or the A3/A4 data decisions. The data screen applies the
same assumed A2 mid-code gate and fixed 1,950 Hz, Q=1 bandpass as the prior
joined replay, then uses its fixed differential-decision phase. There are
63 decisions for 64 A3/A4 input dibits because the first symbol is the
differential reference.

Thus `k=1` is the only tested divisor consistent with both tone and data
*under this D127 phase-step, pulse-width, sample-clock and analog fixture*.
Different per-cycle phase steps, pulse widths, sampling phases or analog
response may change that conclusion. The oscillator-to-8X02 divider,
U10-to-latch clock, DAC bus and analog line route are untraced. This is a
cycle-budget constraint on the candidate transmitter, not a physical clock
measurement or a C2 pass. Keep G2 active and test another photo-compatible
clock/input or receive-output route.

The [machine report](results/photo-tx-cycle-divisor-screen.json) records
each full-state digest, edge schedule, sample hash, bus order, raw and
filtered data-error counts, and source hashes. Reproduce with
`python3 g2/photo_tx_cycle_divisor_screen.py` from the microcode directory.
