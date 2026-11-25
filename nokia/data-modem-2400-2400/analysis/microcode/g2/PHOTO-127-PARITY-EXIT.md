# Held D127 parity selects two control-flow regimes in the q3 fixture

The [controller-frame lane screen](PHOTO-127-CONTROLLER-FRAME-STEPS.md)
found that the A1 frame's distinct third byte `81` leaves the candidate
PC127 phase loop, whereas A0/A2's `88` stays there. The
[full-byte execution](photo_127_parity_exit.py) now runs **all 256 held D127
values**, each for 3,000 real-PROM microinstructions under the same q3,
held-I0, Q=0, upper-bank fixture.

At PC129, every executed read follows the checked relation
`phase_n = (3 + n × D127) mod 256`, with `n` starting at 1. The branch at
PC12A leaves the loop for PC12B exactly when that phase reaches zero.
Because the starting phase is odd, every **odd** D127 value has one such
visit in the first 256 steps; no **even** value can reach zero under a
fixed-byte input.

| Held D127 | PC129 visits before exit | PC12E selected ROM reads | First PC084 wait |
| ---: | ---: | ---: | ---: |
| `01` | 253 | 255 | cycle 2146 |
| `81` | 125 | 255 | cycle 1634 |
| `FF` | 3 | 255 | cycle 1146 |
| `88` | 740 in the 3,000-cycle run | 0 | not reached |

All 128 odd-byte runs follow the PC12A exit with 255 visits to PC12C,
whose selected input is a **scenario constant `1`**. They also make 255
selected upper-bank Am27S31 reads at PC12E, visiting addresses `102–1FF`
then `100`, and reach the PC084 wait. None reaches candidate output words
`392` or `39E`. All 128 even-byte runs keep the four-word PC127 loop for
the 3,000 instructions tested, with 740 PC129 reads and no PC12C/PC12E
visits or PC084 wait. The [machine report](results/photo-127-parity-exit.json)
records every byte, exit timing and trace digest.

The split is an exact **conditional emulator behavior**, not a decoded Nokia
command. D127 may be supplied by another board signal, change during a run,
or select a different Am2901 mapping. The PC12C constant-one input and the
upper-bank choice are scenario assumptions. Still, the `88`→`81` change in
the executed controller frames is a concrete candidate for switching from
a sustained PC127 walk to a finite ROM scan. The next test should vary
the PC12C input source and controller-frame-to-D127 selection while looking
for a reached, changing DAC-bound byte; the present run has no such output.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/photo_127_parity_exit.py
```
