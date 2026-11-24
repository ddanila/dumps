# Reference line samples through the D38E candidate

The photographed [ADC0800PCD](ADC0800-INPUT.md) motivates a byte-wide
receive-input test. [`adc_sample_path.py`](adc_sample_path.py) generates a
32-symbol V.26-ter-class reference waveform: eight zero dibits, sixteen
varying dibits and eight zero dibits, sampled eight times per symbol. The
separate reference receiver recovers all 31 differential decisions. The
signed PCM range is −127…127. Under an explicit symmetric-range hypothesis,
`127 − PCM` approximates the ADC0800's complementary binary output. The
alternative `128 + PCM` tests an inverted bus interpretation.

The runner supplies each of the **256 bytes** at the recurring D read at
microinstruction 38E in the existing photo-constrained q3 fixture (initial
Q=5). It executes the real DSC 2847 control PROMs and the Am27S31 dump.
Both polarities are run in forward and reverse sample order; each case is
clean and consumes one byte per four-word dispatch group.

| Observation | All four candidate runs |
| --- | --- |
| Distinct sample codes | 72 |
| Distinct four-word output groups | 4, selected by current code modulo 4 |
| Post-group states for one code | Exactly one, even when its position/order changes |
| Selected Am27S31 reads after first dispatch | 0 |
| Recovered bits sent to USART | None identified |

The four groups are the same ones found by the earlier complete D-byte sweep:
`0→[11,11,6,6]`, `1→[11,11,16,16]`, `2→[1,1,6,6]`,
`3→[1,1,252,251]`. The per-code state comparison includes the modeled RAM,
Q, flags and sequencer stack after the group. It is identical for each
occurrence of a code in either order. In this fixture, the 38E/38F path
responds to the **current** sample but does not retain the sample history
needed for differential symbol decisions at that observed state. That is a
scoped negative test of this input route, not a rejection of the ADC0800 or
the microprogram's other paths.

The [report and full forward witness](results/adc-sample-path/) preserve the
stimulus, mapping, scenario, trace digest, source hashes and assumptions.
The ADC reference range, conversion timing, D38E connection, photo field
routes, dispatch table and startup Q are unverified. There is no traced
ADC-to-DSC 2847 bus or DSC 2847-to-USART receive-bit path, so this is not
G2's C3 demonstration.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/adc_sample_path.py
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode/g2
```
