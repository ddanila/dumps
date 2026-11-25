# The second ROM scan's bank-dependent value is transient in the q3 fixture

The [PC12C phase scan](PHOTO-12C-PHASE-SCAN.md) establishes an
input-stepped Am27S31 address recurrence at PC12E. The
[paired-bank execution](photo_12c_bank_liveness.py) asks whether its selected
ROM byte affects retained state. Two 3,000-instruction real-PROM runs hold
D127=`81` and D12C=`01` and change only PC12E's Am27S31 A8 bank;
other reads keep the baseline bank. The q3 mapping, held-I0 route and
input bytes remain hypotheses.

Both runs make 255 PC12E reads in the same control-flow sequence. Each
read matches `Y12E = (phase − ROM[bank + phase]) mod 256`, with
`phase = (1+n) mod 256`. The next word follows
`Y12F = (phase + 1 + carry12E) mod 256`.

| Comparison, lower versus upper PC12E bank | Differing visits of 255 |
| --- | ---: |
| Selected ROM byte and PC12E ALU Y | 251 |
| PC12F ALU Y | 69 |
| Retained checkpoint at next PC12C | 69, in R0 only |
| Retained checkpoint after PC12D | 0 |

The PC12D comparison includes all modeled RAM registers, Q, ALU flags,
next PC and stack. The two runs also agree at every later PC084 wait
checkpoint. Thus the bank-dependent byte and carry can affect transient
R0, but the tested loop overwrites that difference before its next ROM
read. This closes **retained ROM feedback in this fixture**; it does not
exclude a physical latch sampling PC12E or PC12F. No controller-to-D12C
connection, DAC clock or analog output is shown. The
[machine report](results/photo-12c-bank-liveness.json) records counts,
checkpoints, trace digests and source hashes.
The [latch-site tone screen](PHOTO-12C-LATCH-TONE.md) tests that transient
sampling hypothesis under explicit clock and DAC-bit assumptions.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/photo_12c_bank_liveness.py
```
