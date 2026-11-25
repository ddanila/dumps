# The split-slice bit relay depends on an unverified upper instruction fan-out

The separated-slice, upper-B [candidate mapping](INDEPENDENT-SLICE-ADDRESSES.md)
translates a shared-field guess into U17/U18 sources for U8's instruction.
That translation assigns **U18 bit 6 to both U8 I2 and U8 I7**. One PROM
output could drive two instruction inputs, but the photographs do not show
those two nets. The [sensitivity screen](upper_i_field_sensitivity.py) tests
this dependency with real control PROMs and Am27S31 bytes, Q=5, zero RAM,
and an assumed D4 controller bit at `38E`. The two photographed candidate
interslice links still supply U8 I4 and I6.

With the original duplicate assignment, a single D4 pulse at input visit
20 changes modeled state at the `38E` checkpoints for visits 20 and 21 and
changes candidate `39E` ALU Y only at visit 21. Substituting each direct U18
bit 0–7 for **either** I2 or I7 gives a `39E` pulse effect only when that
input remains on bit 6. Four of the alternative I2 sources cease selecting
D at `38E`; U18 bits 3 and 5 still select all 128 D bytes and carry the
pulse into two loop checkpoints, but never into `39E`. Every alternative
I7 source still selects D, but none except bit 6 carries the pulse past the
current checkpoint or into `39E`. This is a dependency of the model, not
evidence that the physical board fans out U18 bit 6.

Seven separate one-bit **polarity** flips on unlinked U8 instruction inputs
show how sensitive the loop is to the field guess. Inverting I0 changes the
run from 131 selected ROM reads at three addresses to 390 reads at twelve
addresses. A D4 pulse then changes three ROM **addresses**, but its state
effect lasts only two input checkpoints and it never changes `39E`. Flipping
I5 prevents the recurring input path entirely. None of the seven flips
extends a single-bit pulse beyond two checkpoints. The original mapping and
an I8 flip merely forward the bit one visit later at `39E`; neither produces
a sustained modulator.

The [report](results/upper-i-field-sensitivity.json) records every source,
polarity, D-selection count, ROM-address effect, checkpoint difference and
output difference. Its strongest practical implication is that the earlier
D4→`39E` byte rule rests on **two unresolved U8 instruction connections**.
The next mapping test should constrain those pins from additional photo
evidence or seek a controller-dependent, retained ROM path under another
field candidate. A larger ROM-read count alone is not a function signature.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/upper_i_field_sensitivity.py
```
