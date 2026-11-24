# Recurring D operations beyond 38E

The [inventory and probe](alternate_input_sites.py) traces one representative
initial Q value for each final-PC class in the existing 256-Q sweep, plus Q=0
and Q=5, across five photo-constrained mappings. In 48 real-PROM runs of
2,048 cycles, seven D-consuming sites recur after startup: **127, 12A, 187,
38E, 3A7, 3C1 and 3EB**. This is a route inventory under the declared mapping,
ROM gate and zero-RAM fixture, not a list of measured board input nets.

Eight alternatives outside 38E then receive the same decodable 256-byte
complementary ADC stimulus used in the earlier receiver test, both forward
and reversed. The retained RAM/Q state is measured before the next visit to
the input site. The [saved result](results/alternate-input-sites.json) records
per-case visits, distinct states, ROM reads, addresses and trace digests.

| Mapping and Q | D site | Observed result |
| --- | --- | --- |
| q1/q3, Q=2 | 3EB | All 256 samples consumed; 72 distinct post-site RAM/Q states, but exactly one state per current byte and the same byte→state map in reverse order. No later ROM reads. |
| q1, Q=4 or 255; q3, Q=4 | 3A7 or 3C1 | All samples consumed; one retained state throughout, no later ROM reads. |
| q2, Q=0; q4, Q=8 | 12A | All samples consumed; one retained state. q2 repeatedly reads one fixed Am27S31 address, `101`, rather than sample-dependent addresses. |
| fitted-swapped, Q=1 | 187 | Only 33 forward or 32 reverse samples reach the site before the run reaches 084. The result depends on order, but 187 is inside a PLP/BLT shift loop, so one new ADC sample per visit is a diagnostic timing assumption. |

The q3 Q=4 case has an important bus-versus-operand distinction. D input at
`3A7` makes the Am27S31 **address bus** visit 72 different addresses at
`3B5`, one for each distinct test sample code. At `3B5`, however, the modeled
Am2901 operation does not select the ROM byte as an ALU operand. The updated
report records those unconsumed bus addresses separately from actual ROM
operands. Address variation alone is therefore not a receiver lookup, and
this case still has one retained state and no sample-order history.

The q1 Q=0 path at **127** has a different role in this fixture. A complete
256-value constant-D sweep shows that **only D=00** leaves its recurring 127
loop and enters the changing upper-ROM recurrence at 12C; all other values
stay at 127. The zero case visits 127 once and 12C 500 times in 2,048 cycles,
so it receives no further D127 bytes while producing that recurrence. It is
a trigger, not yet a continuous symbol or sample input to the putative
transmitter.

For fitted-swapped 187, a constant D=00 reaches 084 after eight visits;
constant D=01 keeps the 187/188 loop running for 223 visits in 512 cycles.
The observed order dependence with varying ADC bytes therefore cannot by
itself identify a receiver. It reflects input-sensitive arithmetic and loop
exit under an unverified per-visit conversion schedule. A realistic next test
needs the actual ADC clock/data latch and the processor's D source at that
loop; the current route candidates do not yet show demodulation or recovered
USART bits.

A [held-byte follow-up](ADC0800-INPUT.md) models the ADC0800's latched output
more plausibly. In complete 256-byte sweeps at Q=1 and Q=129, only zero reaches
084 within 512 cycles; nonzero values end back in the 187/188 loop. Thus the
per-visit stimulus above should be treated as a timing diagnostic, not as a
candidate continuous sample schedule.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/alternate_input_sites.py
```
