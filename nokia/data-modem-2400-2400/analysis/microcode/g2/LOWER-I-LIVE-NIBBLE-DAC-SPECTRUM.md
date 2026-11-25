# All sustained D3F8 nibbles miss the direct 1,800 Hz output test

The [held-input analysis](LOWER-I-HELD-NIBBLE-CYCLES.md) found ten D3F8 low
nibbles that keep the `3ED–3FA` ROM loop active. The earlier
[divided-latch screen](LOWER-I-DAC-SAMPLE-CLOCK-SCREEN.md) checked `08/09`
with one 187/188 clock ordering. The
[broader execution screen](lower_i_live_nibble_dac_spectrum.py) checks **all
ten** held nibbles, both 187/188 and 188/187 sample-clock orderings, all 188
integer offsets and four candidate latch data bytes: `3F8`, `3F9`, `3FA`
ALU Y and R10 after `3F7`. It executes the real DSC control PROMs and
Am27S31, then clocks the digital 74LS273 model for 32 samples at 9,600 Hz.

Across 80 source/clock-order/nibble cases and 15,040 full-byte phase
windows, **none** has its strongest non-DC component at 1,800 Hz. The
screen also tries every source bit as the input to 74LS273 D4, using the
photo-derived DAC08 B5←Q4 candidate. None of those 120,320
source-bit/phase windows has its strongest B5 component at 1,800 Hz. A
simple direct source-byte-to-latch route at this divided clock therefore
does not meet the proposed transmitter carrier check for *any* held input
that sustains this loop.

Some 32-sample windows for held nibble `3` or `7` have a DFT peak labelled
2,100 Hz. Their exact sampled code period is **14 samples** at every tested
phase. In the phase-zero examples, the dominant third harmonic of that cycle is
`3 × 9,600 / 14 = 2,057.14 Hz`; the 300 Hz-wide short-window DFT places
it in the 2,100 Hz bin. This is a useful near-tone observation, but it is
not evidence of the required 2,100 Hz answer tone or of a physical output
connection. Held `C` also has a few short-window 2,100 Hz-bin hits; its
period is likewise 14 samples under this clock.

The [result](results/lower-i-live-nibble-dac-spectrum.json) records every
held nibble, both clock orderings, phase hit sets, exact sample periods,
source-bit alternatives, short-window spectra, trace digests and source
hashes. The full DAC bit order, latch D bus, clock, D3F8 input and sequencer
divider remain untraced hypotheses. A different bit permutation, 74LS373
staging, clock phase inside the microword, instruction mapping or output
path is still open. The negative result applies to these direct source-byte
and photo-bit fixtures, not the modem itself.
