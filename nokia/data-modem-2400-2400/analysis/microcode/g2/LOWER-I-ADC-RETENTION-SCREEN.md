# Single lower-instruction pin changes do not retain the D3A1 byte

The [simultaneous-input experiment](DUAL-INPUT-ADC-NIBBLE.md) found a
one-boundary D3A1-to-R7 calculation under two candidate U2 I2 sources. The
[follow-up screen](lower_i_adc_retention_screen.py) changes one lower Am2901
instruction input at a time to each direct U11 data bit (9 inputs × 8 source
bits). It runs the real control PROMs and Am27S31 with controller bits offered
at D38E and a separate ADC-like byte offered at the 21st D3A1 visit. The
physical input routes and U11-to-U2 pin order remain hypotheses.

Of 72 single-pin mappings, 42 reach the 320-microinstruction comparison
window with enough D3A1 visits. The other 30 do not reach a sample visit plus
two later visits in that window; this screen makes no retention claim for
those paths. Five mappings select both offered inputs on 23 visits each:
U2 I2 supplied by U11 bits **0, 2, 3, 4 or 7**. All five preserve the PC path.

For each of those five, D3A1=`01` or `FF` changes the full modeled state only
at the offered byte's loop boundary (visit 20). D3A1=`80` has no effect there.
At the next and later observed D3A1 boundaries, each state equals its zero-byte
control. None of these probes changes a selected ROM address or any reached
candidate output ALU event at `392–39F`. This rules out a retained receive
sample **under these single-pin alternatives and this Q=5, zero-RAM fixture**;
it does not rule out a different input phase, multiple pin changes, another
startup state or an ADC path elsewhere in the program.

The [machine report](results/lower-i-adc-retention-screen.json) records every
candidate, reached-site counts, boundary differences, trace digests and source
hashes. The next useful search is a jointly changed instruction/address or
timing candidate that carries an ADC-derived value to a later loop state; a
missing continuity measurement is not a prerequisite.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/lower_i_adc_retention_screen.py
```
