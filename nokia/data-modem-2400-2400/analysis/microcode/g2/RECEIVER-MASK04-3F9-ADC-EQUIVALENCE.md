# At the tested capture visits, `3F9`/`3FA` Y recode the current ADC high nibble

The [cross-fixture check](receiver_mask04_3f9_adc_equivalence.py) applies
the earlier [executed `3F9`/`3FA` codebook](JOINT-MASK04-RECEIVE-3F9-3FA-CODEBOOK.md)
without refitting it. It reconstructs the ADC bytes for eight independent
legal-carrier PROM traces (two phases, three payload seeds, and a 0.85-gain,
one-sample-offset variant), verifies the saved ADC hashes where present,
and uses the saved ADC bytes and executed Y values for both ROM-sensitive
`12A` buffered-loopback traces. The independent carrier traces and
buffered traces are the same ones used by the previous
[full-byte readout screen](RECEIVER-MASK04-3F9-FULLBYTE-SCREEN.md).

At visits 46 and 93 of each saved symbol, **all 640 captured Y bytes**
(`3F9` and `3FA` for 320 ADC samples) match the prior codebook entry
for that sample's **current ADC high nibble**. All 16 high-nibble values
occur. The only indistinguishable high-nibble pair in the combined
`3F9`/`3FA` codebook is `9`/`D`: both produce `31/20`.

This explains why adding bits to a fixed-pair `3F9` lookup did not reveal
an onboard dibit decision. Under these tested fixtures and capture visits,
the two Y bytes are a deterministic recoding of the current quantized
sample; a temporal decoder built from them is an **external** sample
processor, not evidence that the microprogram emitted a recovered bit.
The result does not rule out useful Q/RAM state, other executed words,
different capture visits, or a physical output circuit. Next trace the
post-`3F9` Q/RAM state through a complete symbol transition and identify
a mode-qualified or later output that actually consumes history. Keep
the ADC and output routing as labeled assumptions; C3 and G2 stay open.

The [machine report](results/receiver-mask04-3f9-adc-equivalence.json)
records each trace, nibble coverage, observed code map and alias pair.
Reproduce with `python3 g2/receiver_mask04_3f9_adc_equivalence.py`.
