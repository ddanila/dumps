# The history-sensitive `3FA` high nibble is exactly a three-sample delay transform

The [equation replay](receiver_mask04_ram_return_delay_equation.py)
reexecutes the two legal-carrier, 192,047-word high-return runs from the
[RAM-return screen](RECEIVER-MASK04-LEGAL-RAM-RETURN.md). Both full trace
digests and `3FA` Y hashes match the saved runs. In each held ADC sample,
executed `3F9` Y is constant across all 47/46 visits.

For sample index `s ≥ 3`, the **high nibble of every executed `3FA` Y**
obeys this exact relation:

```text
Y3FA_high(s) = (Y3F9_high(s − 3) + 0x20) & 0xF0
```

The first three samples, 141 visits, produce `20` high because the
candidate RAM is initialized to `01`. Across the two legal streams,
the equation matches **12,000/12,000 `3FA` visits** with no high-nibble
exceptions. The observed high-code pairs are `10→30`, `20→40`,
`30→50`, `40→60`, `70→90`, and `90→B0`. The low bit is outside this
equation; it is one on 422 and 655 visits in the two streams. The
[earlier `3FA` arithmetic audit](JOINT-MASK04-RAM-CARRY-ARITHMETIC.md)
identifies the low bit with the ALU carry input under its corresponding
RAM-return fixture.

The RAM return really enters an executed operand and makes Y depend on
past samples, but **its high output here is a recoded, fixed three-sample
delay of the input**, not an adaptive echo estimate or a recovered
dibit. The low bit and other output sites still need separate tests.
Next challenge another photo-compatible return/mode route that places
a varying trained coefficient on a consumed operand, and trace any
candidate receive bit to USART-01. RAM, latch, TEST and output wiring
remain assumptions; C3/C4 and G2 stay open.

The [machine report](results/receiver-mask04-ram-return-delay-equation.json)
contains trace hashes, the checked equation, per-stream code maps and
low-bit counts. Reproduce with
`python3 g2/receiver_mask04_ram_return_delay_equation.py`.
