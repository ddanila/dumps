# A candidate control link between the two Am2901s

The [front photograph](../../../photos/PXL_20261123_114926601.jpg) shows an
isolated bright track across the gap between U8 and U2. Rectified at
4000×2000, a four-neighbor bright-pixel component from `(3027,1500)` spans
`(3007,1358)–(3031,1533)`. It approaches one U8 facing pad and one U2
facing pad, with dim gaps at both pads. The [highlighted crop](results/photo-slice-link/candidate.jpg)
and [reproducible probe](photo_slice_link.py) preserve the observation and
photo hash. This is a **candidate connection**, not measured continuity.

The packages have the same visible orientation. Under the existing U2 pin
attribution and [AMD's P-40/D-40 top-view diagram](https://deramp.com/downloads/mfe_archive/050-Component%20Specifications/AMD/2900%20Family/amd-2901b-c.pdf),
the two pad vicinities correspond to **U8 pin 28 (I4)** and **U2 pin 13
(I1)**. If that interpretation and the connection are correct, these two
control inputs share a net. The photos do not show what drives it.

The current emulator represents U8 and U2 as one 8-bit Am2901 with a shared
nine-bit instruction. In that model, this candidate net requires I4=I1.
The [screen](results/photo-slice-link.json) compares those bits in all 1,024
real control-store words and in a 1,580-cycle controller-bit-driven run under
each of the five current photo-constrained mappings:

| Mapping | Nonblank words with I4≠I1 | Executed cycles with I4≠I1 |
| --- | ---: | ---: |
| q1 | 498 | 292 |
| q2 | 502 | 780 |
| q3 | 503 | 286 |
| q4 | 501 | 781 |
| fitted-swapped | 501 | 525 |

Thus **none of these shared-instruction interpretations accommodates the
candidate net**. This does not rule out the board or show that the microcode
cannot work: the pin interpretation or photo connection may be wrong, and the
two 4-bit slices may instead receive different instruction words. The next
useful test is to trace another control input on both packages or model
independent slice instructions under explicit candidate wiring. This result
is a constraint on the current model, not a demonstrated modem function.

Reproduce with:

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/photo_slice_link.py
```
