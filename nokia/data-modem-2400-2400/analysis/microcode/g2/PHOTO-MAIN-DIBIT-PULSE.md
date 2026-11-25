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

The unchanged DSC PROMs then run for 96,256 consecutive microinstructions
for each of four real controller USART streams. Every run remains in the
upper-bank PC127/129 loop and verifies all **24,054** selected PC129 ROM
addresses, bytes and Am2901 Y values against the cumulative phase recurrence.
Each of the first eight dibits gives the expected retained phase offset; all
four dibit values occur in the real streams. The seven candidate DAC samples
after each pulse keep the same per-sample phase increment `D0` (208 decimal),
the aliased 1,800 Hz carrier step at 9,600 samples/s.

| Controller selector | First eight dibits | Cumulative phase offset after each dibit |
| --- | --- | --- |
| `00` | `2 1 0 0 0 2 3 3` | `40 00 00 00 00 40 C0 40` |
| `20` | `3 1 2 3 3 2 3 1` | `80 40 80 00 80 C0 40 00` |
| `40` | `1 2 3 3 3 1 0 0` | `C0 00 80 00 80 40 40 40` |
| `60` | `0 2 3 3 3 1 0 0` | `00 40 C0 40 C0 80 80 80` |

The projected full DAC-code spectra over these **eight-symbol bursts** peak
at 1,770, 2,050, 1,910 and 2,380 Hz, respectively. The independent
raised-cosine reference on the same short dibits peaks at 1,770, 2,060,
1,920 and 1,920 Hz. A short varying-data burst therefore cannot be used as
a strict 1,800 Hz peak check; the fourth candidate also differs substantially
from its reference. The candidate DAC bus and clock are untraced, and the
four-visit rule makes abrupt phase jumps without a demonstrated pulse-shaping
filter. This is a **conditional four-way phase lead**, not a C2 transmitter
pass or a line-output waveform.

The [machine report](results/photo-main-dibit-pulse.json) records all four
controller dibit sequences, phase checkpoints, first DAC codes, width screen,
spectra and source hashes. Next constrain the pulse/gate wiring and sample
capture from board evidence, then run a longer controller data interval and
compare its candidate DAC bytes with the reference, including the required
segment-1 180° reversals. Keep the receiver and echo paths open as separate
G2 requirements.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/photo_main_dibit_pulse.py
```
