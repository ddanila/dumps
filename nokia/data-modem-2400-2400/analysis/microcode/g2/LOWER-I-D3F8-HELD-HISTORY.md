# A held D3F8 input retains earlier byte history in the ROM loop

The `389–3A1` candidate lost ADC history at the next loop boundary. The
separate [D3F8 held-history screen](lower_i_d3f8_held_history.py) follows the
real-PROM `3ED–3FA` loop under the previously tested photo-compatible
instruction/data mapping. In this fixture D3F8 is selected by the ALU every
**eight microinstructions**. With the photographed 14.4 MHz oscillator and
one oscillator period per microinstruction, a 9,600 Hz held sample spans
1,500 microinstructions, so sample holds alternate **188 and 187 D3F8
visits**. The clock relation, D3F8 source and mapping remain hypotheses.

The [saved matrix](results/lower-i-d3f8-held-history.json) tests all 64
transitions between the eight odd low-nibble bytes `01…0F`, with the first
byte held for 188 visits and the later byte held for the rest of a
6,000-microinstruction run. D0 stays high, as required to keep this tested
loop active; this is a **biased diagnostic input**, not the raw ADC0800
output. Thirty-six transitions leave the repeated path before the 745th
D3F8 visit. Twenty-eight remain on the same long PC path as the steady
later-byte control. Of those, **19 retain a different final modeled state**.

The clearest witness compares `01` for the first 188 visits followed by
`03` against steady `03`. Both runs reach 745 selected D3F8 visits, see the
**same input from visit 188 onward**, and execute the same PC sequence.
Nonetheless, their RAM/Q/ALU/next-PC/stack boundary snapshots differ at all
557 remaining visits, through visit 744. The difference persists past the
next shared sample boundaries at visits 375 and 563. After the input becomes
equal, **1,034/1,112 selected ROM-address events** and **1,512/1,669
candidate ALU-output events** differ. Their final modeled states differ.
The later ROM and Y differences therefore reflect retained internal history
under this mapping, rather than a changed current byte or an early branch.

This is a materially stronger receive-side lead than a one-byte relay, but
it does **not** identify the loop as a demodulator. The tested odd nibble
classes are not a reference line waveform; D0-high bias, ADC-to-D3F8 wiring,
sample clock, PROM-to-Am2901 fields and output route are untraced. No bit
decision reaches the controller's USART-01 receive input, so C3 remains
open. The next test should feed a continuous complementary ADC0800 sample
stream through a labelled D3F8 bias/bit mapping, check that the loop remains
active, and seek a reproducible decision or output correlated with the
known transmitted dibits. Compare against a time-reversed or phase-shifted
control to avoid mistaking generic state sensitivity for demodulation.
