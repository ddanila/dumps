# Raw PROM bits do not isolate the table consumers as a sample clock

The [diagnostic latch replay](PHOTO-TABLE-OUTPUT-ORDER.md#diagnostic-latch-at-the-internal-consumers)
tentatively clocks the DAC-side 74LS273 when the microcode visits `140` or
`146`. Those sites carry controller-dependent table bytes, but the actual
latch clock is untraced. The [edge screen](photo_output_clock_bit_screen.py)
asks whether any **single raw data output** of the four control PROMs could
directly supply a rising clock at every such visit.

The screen replays q3 with the inverted-U10-bit-5 U5 hypothesis, real 8031
selector-`20`/other saved line bytes at D349, three strict branch seeds and
15 diagnostic AC=RST pulses. All 12 real-PROM traces complete the existing
stack/restart contract. It checks both edge directions on all 32 PROM data
bits as consecutive microinstructions execute.

| Edge class present at every `140`/`146` visit | Bits | Edges per 2,500-cycle run | Median gap (cycles) |
| --- | --- | ---: | ---: |
| Rising | U11 D1, D3; U17 D3, D5; U18 D3, D7 | 164–411 | 3–9 |
| Falling | U10 D2, D4 | 167–333 | 4–7 |

The 74LS273 is rising-edge triggered, so the falling-edge rows are not direct
clock candidates without inversion. The six rising candidates all fire at
the consumer words, but each also fires hundreds of times elsewhere. If the
14.4 MHz oscillator yields one microcycle per `k=1…4` oscillator periods and
the DAC takes one sample at the hypothesized 9,600 Hz, a sample interval is
`1500/k = 375…1500` microcycles: only about 2–7 sample clocks would occur in
2,500 cycles. None of these **bare PROM bits** has that cadence. This timing
comparison is conditional; neither the divider nor the DAC update rate has
been measured.

The `140`/`146` visits themselves are also sparse and irregular: for selector
`20`, seed 155 visits them at cycles 296, 302, 355, 360, 728, 733; seed 183
at 732, 738; seed 184 at 179, 184, 271, 277, 1824, 1830. A decoded or
gated clock could isolate these sites, but their current repeat pattern is
not a sustained 9,600 Hz sample stream. The result directs the next output
test toward a clock decoder, divider, or a different repeated microcode path;
it does not identify the physical 74LS273 clock or reject an intermediate
register role for any PROM bit.

The [report](results/photo-output-clock-bit-screen.json) contains all 64
bit/direction summaries, the 12 trace digests and source hashes. The input,
U5 latch capture, branch bus and diagnostic restart remain labelled
assumptions. No DAC waveform or receiver/echo path is established.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/photo_output_clock_bit_screen.py
```
