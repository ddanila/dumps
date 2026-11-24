# Changing D38C reaches R6 but does not survive the loop

The [independent-slice screen](INDEPENDENT-SLICE-FIELDS.md) found 127
controller-fed ROM-operand selections after the first input in two
photo-inspired separated-lane layouts. A trace locates all of them at
microinstruction `38C`, reading Am27S31 address `106`, byte `13` (hex). It is the
**lower U2 slice's changed instruction** that selects D there; the upper U8
instruction is independent but does not select D at that word. This corrects
the earlier description of the read as upper-slice selection.

The [D38C perturbation probe](independent_slice_d38c.py) replaces that one
ROM-read policy with an explicitly hypothetical stream of 128 D bytes. It
keeps the same 128 real 8031 scrambler bits at D38E and compares five D38C
stimuli in each separated layout: constant `13`, a generated 8-sample/baud
reference line waveform encoded as `127 − PCM` for a candidate ADC0800
complementary bus, its reversal, and both orders of the inverted-bus
alternative `128 + PCM`. The ADC coding, dual source schedule and D38C route
are assumptions, not traced Nokia wiring.

| Observation | Both separated layouts |
| --- | --- |
| D38C visits and D38E controller-bit visits | 128 each per 1,580-cycle run |
| Distinct offered reference ADC bytes | 56 |
| Distinct R6 values just after D38C | 16, versus one for constant D |
| R6 just after each `3A0` | One fixed value per layout (`FB` or `0B`) |
| Full RAM/Q/previous-Y/flags/stack/next-PC differences at `3A1` versus constant D | **0 of 128** boundaries, for every varying stimulus |
| Candidate output Y at reached `39E` | Fixed `0B` |

Thus D38C does affect the modeled arithmetic and writes R6, but the later
`3A0` write removes that difference before the next `3A1` loop boundary.
The complete modeled boundary state is identical in forward/reverse and both
byte-polarity runs, so this specific recurring path does not retain receive
sample history or produce changing output. It does **not** rule out another
ADC input site, a different lane mapping, a different loop continuation or an
echo-canceller path. It means the extra ROM reads opened by the separate-slice
model do not, by themselves, meet G2's receive or transmit checks.

The [report](results/independent-slice-d38c.json) records the first D/R6
writes, per-layout overwrite value, trace digests, assumptions and source
hashes. The next input experiment should target a word whose D-dependent
register survives to the following iteration or changes a reached output.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/independent_slice_d38c.py
```
