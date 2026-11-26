# A delayed MCM93422 return makes `3FA` Y history-sensitive on legal carriers

This [real-PROM replay](receiver_mask04_legal_ram_return.py) runs two
independent legal V.26-ter-style receive streams through the mask-04
four-row loop. The labeled external-memory hypothesis latches the high
nibble of executed `3F9` Y, writes it through a sample-paced MCM93422
address, and returns the value from address offset −3 on `3FA` D.
The TEST choice is previous carry with polarity one, which sustains
this route. RAM pins, write clock, latch, read mux and TEST source remain
untraced assumptions.

Each carrier gets three full 192,047-word controls: read-only memory
(initial value `01`), write-only memory, and write plus delayed return.
All six runs complete 6,000 ADC visits. Read-only and write-only give
**identical `3FA` Y bytes**. Enabling both write and return changes
**5,859/6,000** Y bytes on each carrier. The first changed return is at
visit **141**, three 47-visit held samples after the start; the captured
first noninitial RAM read is `31` from address `01`.

The audit also matches the first visit of samples with the same exact
current ADC byte and 0–7 symbol sample position, requiring different
preceding ADC bytes. In **21** such groups, read-only and write-only
have no `3FA` Y variation, while the delayed-return route varies in
**9** groups. For example, one matched group yields `3FA` Y=`B0`
after preceding ADC `F2` but Y=`40` after `4C`, even though the
current ADC byte and sample position match.

This is a causal **external-memory → consumed D operand → executed Y**
path on legal symbol waveforms under the stated wiring. It supplies a
history-sensitive candidate output that the direct `3FA` mode did not.
It does **not** yet show differential dibit decisions, a USART RxD
signal, or falling echo residual; the changed Y may simply recode a
delayed sample. Next freeze a circuit-like temporal decision from this
stream using independent legal training carriers, then challenge new
payloads and the ROM-sensitive buffered line. In parallel, compare
own/remote/mixed training controls at a candidate analog residual.
C3/C4 and G2 remain open.

The [machine report](results/receiver-mask04-legal-ram-return.json)
records every trace hash, control contrast and matched-group witness.
Reproduce with `python3 g2/receiver_mask04_legal_ram_return.py`.
