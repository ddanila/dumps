# Changing A1 frames switch a candidate DSC tone without resetting the microcode

The [held-A1 controller run](A1-COUNTER-PHASE.md) emits `80 02 A1 7A` for
eleven polling iterations, then `80 02 81 7A` while still in A1. This replay
applies those **ROM-executed frame bytes** to the [photo-compatible but
untraced chip-1 decode](PHOTO-CONTROLLER-MODE-DECODE.md): logical CD4094
chip-1 bit 5 selects DSC D127=`B0` for `A1` and D127=`88` for `81`.

For each of the four controller selector classes, the unchanged DSC PROMs run
for 220,000 consecutive microinstructions under the q3 mapping. D127 changes
on the calculated PC127 visit; the DSC registers, phase and sequencer are not
reset. The calculation uses the observed controller iteration-completion
cycle difference, its 11.9808 MHz oscillator divided by 12 per 8031 machine
cycle, the DSC's 14.4 MHz oscillator, one oscillator period per candidate
microinstruction, and four microinstructions per PC127 loop. No physical
clock relationship or frame-latch instant has been measured.

| Controller selector | 8031 cycles to byte change | D127 switch visit | DAC-code samples before/after | Peak before→after | Fit at target before/after |
| --- | ---: | ---: | ---: | --- | --- |
| `00`, `40` | 7,835 | 28,251 | 76 / 71 | 1,800→2,100 Hz | 0.598 / 0.364 |
| `20`, `60` | 7,813 | 28,172 | 76 / 71 | 1,800→2,100 Hz | 0.598 / 0.282 |

Each run visits PC127 and upper-bank PC129 54,990 times, without emulator or
stack errors. Every PC129 visit matches the phase recurrence, selected
Am27S31 address and byte, and Am2901 Y result, including the first visits on
both sides of the mode change. Candidate DAC codes use the separately
labelled Y129→74LS273→DAC08 Q4/Q5-swapped bus order and one capture per 375
PC129 visits, which corresponds to 9,600 samples/s **under the assumed clock**.
The table's fit is the fraction of code variance explained by a single sine
at the named frequency; the 1,800 and 2,100 Hz peaks are measured from the
executed code sequence, not inserted waveforms. The
[machine report](results/photo-a1-dynamic-mode-replay.json) records the
switch trace, exact spectra, first DAC codes, input scenario and source
hashes.

This is a viable **conditional transmitter lead**: the candidate controller
decode can switch a continuously running microcode phase walk from the
1,800 Hz carrier to a 2,100 Hz state. It does not prove that Nokia wired
CD4094 chip 1 to D127, that the LS273 samples Y129 at 9,600 Hz, or that this
DAC08 stream reaches the line. It also does not show dibit phase modulation,
the natural A1 duration, receiver operation, or echo cancellation. The next
test must put the real USART dibits and this time-varying command into **one**
stateful run and look for 1,200-symbol/s phase changes while keeping the
carrier and DAC path explicit.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/photo_a1_dynamic_mode_replay.py
```
