# Mask-04 receive rows calculate an ADC-dependent ROM address and retain Q in R1

The [joint four-row comparison](JOINT-FOUR-ROW-RETENTION-TX.md) found that
lower-field mask `04` retains ADC-dependent RAM/Q state after `3FE`, whereas
mask `08` erases it. This follow-up reconstructs each executed register write
and checks the arithmetic against four complete real-PROM traces: two
32-sample complementary ADC waveforms under each map. Both maps execute
48,047 instructions per waveform, with 1,500 `3F8` ADC visits and 6,001
`3EB` wrapper visits. The paired waveforms take identical PC paths.

At `3F8`, mask `04` executes low/high Am2901 instructions `D4/C5` with
register address A=5. For all 1,500 visits in each waveform, the traced
Y byte equals the following expression, where `D` is the selected ADC byte,
`r` is R5 *before* the word, and `c` is the traced low-slice carry input:

```text
lo = ((~r) & 0x0f) + c
hi = (D >> 4) + (r >> 4) + (lo >> 4)
Y  = (lo & 0x0f) | ((hi & 0x0f) << 4)
```

This uses the ADC **high nibble** in the high slice; its low nibble is not
used in this checked equation. On the next word, `3F9`, the executed
external read selects Am27S31 address `0x100 + Y` and returns the matching
real-ROM byte on every visit. Thus the ADC is part of an executed table
lookup, not just a value stored in a diagnostic trace.

At `3EB`, mask `04` executes low/high instructions `92/97` with scenario
input D=`01` and carry-in 1. After each of its 6,001 visits per waveform,
R1 equals `(- (Q_before & 0x0f)) & 0xff`. This makes R1 a sign-extended
negative of Q's previous low nibble. Between the paired waveforms, Q
differs before `3EB` on 2,483 wrapper visits and R1 differs on exactly
those 2,483 visits. Complete RAM/Q state still differs after `3FE` on
1,312/1,500 visits.

Mask `08` provides a nearby control. Its `3EB` instructions are `94/C7`;
Q differs on 1,253 wrapper visits between the same waveforms, but R1 is
`0x10` on every wrapper visit and complete state reconverges after `3FE`
on all 1,500 visits. Its `3F8` instructions are `D6/D5`; the `3F9` ROM
read remains live, so the distinction is the executed arithmetic and
retention, not a missing ADC fixture.

The field map, split-slice links, ADC gate, TEST source, dispatch schedule
and D=`01` wrapper input are labelled board hypotheses. These checks
explain why mask `04` is a stronger receive *candidate*; they do not prove
the Nokia wiring or identify a received bit. C3 remains open. The next
useful experiment must find an executed decision or output route from this
retained state, or change the mapping/input hypothesis.

The [machine report](results/joint-mask04-adc-rom-wrapper-rule.json) records
instruction pairs, equation counts, state contrasts, trace digests and
source hashes. Reproduce with
`python3 g2/joint_mask04_adc_rom_wrapper_rule.py` from the microcode
directory.
