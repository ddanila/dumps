# The second q3 loop also advances a ROM address by its selected input

The [D127 parity run](PHOTO-127-PARITY-EXIT.md) showed that a held odd
D127 byte reaches PC12C, where the previous fixture supplied the constant
input `1`. The [PC12C input screen](photo_12c_phase_scan.py) keeps D127=`81`
to enter that path, then runs **all 256 held PC12C input bytes** through
3,000 real-PROM microinstructions each. The q3 Am2901 mapping, held I0,
Q=0 startup, upper-bank ROM read and byte sources are labelled hypotheses.

Every selected PC12E Am27S31 address matches
`0x100 + ((1 + n × D12C) mod 256)`, where `n` starts at 1. For odd D12C,
the index reaches zero once within 255 reads and the program later waits at
PC084. For even D12C, the index cannot reach zero from the odd start value;
the loop continues through the 3,000-instruction run.

| Held D12C | PC12E ROM reads | Address order | First PC084 wait |
| ---: | ---: | --- | ---: |
| `01` | 255 | `102, 103, …, 1FF, 100` | cycle 1634 |
| `03` | 85 | `104, 107, …, 1FD, 100` | cycle 954 |
| `FF` | 1 | `100` | cycle 618 |
| `02` | 613 in the bounded run | `103, 105, …` | not reached |

All 128 odd-byte cases finish the scan; all 128 even-byte cases keep reading
at PC12E. The odd cases visit distinct addresses and end at `100`; the
even cases visit a repeating subset. None reaches candidate output words
`392` or `39E` under this fixture. The
[machine report](results/photo-12c-phase-scan.json) contains every input
byte, read count, first addresses, wait timing and trace digest.

The code therefore implements **two serial input-stepped address loops**
under this mapping: D127 advances the first, and the selected PC12C input
advances the second. This is a stronger behavioral description than calling
either loop a carrier or filter from a tone-like spectrum. PC12C's input
source and the ROM-data consumer are still untraced; a different input
schedule or latch phase could make these loops do useful signal work. A
next test should feed a changing, controller-derived source at PC12C and
check whether ROM values survive into a reached output or state register.
The [paired-bank liveness check](PHOTO-12C-BANK-LIVENESS.md) finds only a
transient R0 difference under the current fixture; the state matches after
PC12D. A hypothetical external latch remains a separate output test.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/photo_12c_phase_scan.py
```
