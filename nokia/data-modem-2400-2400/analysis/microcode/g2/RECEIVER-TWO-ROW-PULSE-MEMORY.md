# Interleaved ADC path retains four input-dependent state classes

The [interleaved `3EF/3F7` schedule](RECEIVER-DISPATCH-SOURCE.md#a-two-row-index-schedule-survives)
passes ADC samples into real Am27S31 lookups, while the
[fixed-phase decision screens](RECEIVER-TWO-ROW-DECISION.md) find no dibit
output. The [pulse replay](receiver_two_row_pulse_memory.py) asks whether
one changed sample is retained through the two-row program, and how the
retained state depends on the input code.

Every paired run executes 48,047 real-PROM microinstructions, selects
3,000 modeled ADC bytes at `D3F8`, and has the same PC path. The control
offers `09` on every visit; a trial replaces one visit, or a 93/94-visit
sample-length window, then offers `09` again. Q, all 16 RAM bytes, Y at
`3FA`, and the next `3F9` ROM address are compared after every ADC visit.
The `0/2` dispatch index, complementary ADC input route and conversion
schedule are explicit hypotheses.

At visit 100, changing only the ADC high nibble gives four late state
classes. The table groups all fifteen high-nibble alternatives by the
**final** modulo-256 difference from the `09` control:

| Final `3F9` address offset | Final Q offset | One-visit pulse bytes | Later state behavior |
| ---: | ---: | --- | --- |
| 0 | 0 | `59`, `69`, `D9`, `F9` | Reconverges by at most two later visits |
| 1 | 4 | `29`, `39`, `49`, `79`, `89`, `99`, `B9` | Differs through visit 2,999 |
| 2 | 6 | `A9`, `E9` | Differs through visit 2,999 |
| 3 | 8 | `19`, `C9` | Differs through visit 2,999 |

All eleven persistent cases also finish with RAM12 displaced by `F0`;
RAM10 and RAM11 offsets equal the ROM-address offset. For the persistent
cases, the final 500 ROM-address differences are all the same 1, 2 or 3.
One `19` pulse placed at visits 10–14 gives the same final Q offset 8 and
ROM-address offset 3 every time. One-visit `59` pulses at visits 10–14
and 100–104 instead affect only the pulse visit and one following visit.

The effect also survives an assumed converter hold: replacing 94 visits
starting at 188 with `19`, or 93 visits starting at 282 with `A9`, leaves
the state and next ROM address different on **every** remaining visit after
the input returns to `09`. A held `59` window leaves at most one changed
visit after return. Thus the extra `3EF` row does **not** simply erase all
ADC history. It transforms some high-nibble inputs into persistent,
quantized modeled state offsets while other inputs reconverge.

These offsets are not a decoded DPSK quadrant, carrier phase, echo tap or
USART bit without further evidence. The sweep holds the low nibble at `9`,
starts from one Q/RAM seed and one dispatch schedule, and does not model the
physical ADC or output route. A useful next test is to follow these Q/RAM
and ROM-address state classes under actual changing reference samples,
then test a **multi-sample** decision that generalizes across held-out
streams rather than reading one fixed-phase bit.

The [machine report](results/receiver-two-row-pulse-memory.json) includes
all pulse windows, per-register differences, late ROM-address histograms,
trace digests and source hashes. Reproduce it with:

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/receiver_two_row_pulse_memory.py
```
