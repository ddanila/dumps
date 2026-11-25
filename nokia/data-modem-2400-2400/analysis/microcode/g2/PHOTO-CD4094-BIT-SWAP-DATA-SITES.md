# The A1 bit-swap loop has a tone-rate phase ramp, not a recovered sine DAC byte

The [two-wire candidate](PHOTO-CD4094-BIT-SWAP-TONE.md) maps the A1 CD4094
byte `81→88` at D127 and stays in the q3 `127–12A` loop. The
[source screen](photo_cd4094_bit_swap_data_sites.py) executes that held byte
through 3,000 real-PROM microinstructions with each Am27S31 bank. All 740
`129` reads per bank check the phase, selected ROM byte, ALU Y, carry and
following `12A` Y against the recurrence. It then projects 640 captures at
the hypothetical 9,600 Hz gate, testing all 32 start-phase alignments for
one or three oscillator periods per microinstruction. All alignments are
spectral rotations.

| Candidate full DAC byte | Upper-bank peak, divisor 1 | 2,100 Hz variance fraction | Upper-bank peak, divisor 3 |
| --- | ---: | ---: | ---: |
| R1 phase | 2,100 Hz | 0.610480 | 3,900 Hz |
| Selected ROM byte | 3,000 Hz | 0.155195 | 4,200 Hz |
| `129` ALU Y | 2,100 Hz | 0.345587 | 3,900 Hz |
| `12A` ALU Y | 2,100 Hz | 0.608836 | 3,900 Hz |
| `129` carry as a byte | 2,100 Hz | 0.246099 | 3,900 Hz |

The lower bank gives the same 2,100 Hz peak for phase, `129` Y and `12A` Y
at divisor 1; its ROM byte instead peaks at 3,300 Hz. At divisor 3, the
lower-bank ROM byte does peak at 2,100 Hz, but only 0.170856 of its variance
is at that bin. The [machine report](results/photo-cd4094-bit-swap-data-sites.json)
also records the candidate DAC B5-bit spectra and execution digests.

The `12A` result is nearly the raw phase ramp because the ROM affects it
only through a one-bit carry: `Y12A = phase + 1 + carry129`. The selected
ROM byte itself does not yield a dominant 2,100 Hz upper-bank full-byte
stream. Thus the bit-swap scenario supplies a **tone-rate phase walk**, but
none of these directly sampled bytes establishes a low-distortion sine DAC
code. An analog filter or another digital stage could change the final line
waveform; neither is traced here. Keep the D0/D3 crossing, DAC byte source,
clock qualification and full latch wiring as separate hypotheses, and seek
a physically supported source or downstream shaping path. This result does
not demonstrate dibit modulation or receiver/echo processing.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/photo_cd4094_bit_swap_data_sites.py
```
