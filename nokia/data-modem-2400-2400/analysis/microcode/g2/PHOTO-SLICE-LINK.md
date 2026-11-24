# Two candidate control links between the Am2901s

The [front photograph](../../../photos/PXL_20261123_114926601.jpg) shows two
separate bright tracks across the gap between U8 and U2. Rectified at
4000×2000, four-neighbor bright-pixel components from `(3027,1500)` and
`(2972,1500)` span `(3007,1358)–(3031,1533)` and
`(2934,1342)–(2977,1537)` respectively. Each approaches one U8 facing pad
and one U2 facing pad, with dim gaps at the pads. The
[highlighted crop](results/photo-slice-link/candidate.jpg) and
[reproducible probe](photo_slice_link.py) preserve the observations and photo
hash. They are **candidate connections**, not measured continuity.

The packages have the same visible orientation. Under the existing U2 pin
attribution and [AMD's P-40/D-40 top-view diagram](https://deramp.com/downloads/mfe_archive/050-Component%20Specifications/AMD/2900%20Family/amd-2901b-c.pdf),
the first pair of pad vicinities corresponds to **U8 pin 28 (I4)** and
**U2 pin 13 (I1)**. The second corresponds to **U8 pin 26 (I6)** and
**U2 pin 14 (I2)**. If those interpretations and connections are correct,
each pair shares a net. The photos do not show what drives either net.

The current emulator represents U8 and U2 as one 8-bit Am2901 with a shared
nine-bit instruction. In that model, the candidate nets require I4=I1 and
I6=I2. The [screen](results/photo-slice-link.json) compares those pairs in
all 1,024 real control-store words and in a 1,580-cycle controller-bit-driven
run under each of the five current photo-constrained mappings:

| Mapping | Nonblank words with either mismatch, of 1,021 | Executed cycles with either mismatch, of 1,580 |
| --- | ---: | ---: |
| q1 | 810 | 804 |
| q2 | 832 | 929 |
| q3 | 817 | 806 |
| q4 | 828 | 930 |
| fitted-swapped | 822 | 928 |

The report also gives separate counts for each pair: I4≠I1 occurs in
498–503 nonblank words, and I6≠I2 in 614–639. The second visible track thus
provides an independent check on the first photo interpretation.

Thus **none of these shared-instruction interpretations accommodates the
candidate nets**. This does not rule out the board or show that the microcode
cannot work: the pin interpretation or photo connection may be wrong, and the
two 4-bit slices may instead receive different instruction words. The next
useful test is to model independent slice instructions under explicit
candidate wiring and see whether controller-driven ROM reads and line-output
samples emerge. The [first executable split-slice test](SPLIT-SLICE-PROBE.md)
does that for these two links; it still finds no changing candidate output in
its declared fixture. This is a constraint on the current model, not a
demonstrated modem function.

Reproduce with:

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/photo_slice_link.py
```
