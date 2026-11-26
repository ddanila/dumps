# A row-0-qualified latch preserves the mask-04 receive byte

The [event replay](receiver_mask04_u12_latch_replay.py) tests a concrete
continuation of the previously identified raw-PROM `3ED` gate. It executes
192,047 real-PROM cycles for each of two complementary-ADC streams with the
same random dibits and initial state: reference carrier at 0° and 45°.
The independent reference receiver recovers both streams. Trace digests and
the qualified decoder results agree with the earlier
[phase-47](RECEIVER-MASK04-PHASE47-BOOLEAN-DIBITS.md) and
[carrier-phase](RECEIVER-MASK04-CARRIER-PHASE-SCREEN.md) runs.

The raw three-bit PROM decode has 24,000 falling level transitions per run,
one after every executed `3ED`; the first four `3ED` cycles are 50, 58, 66
and 74. The assumed U12 data pins take Y bits 0–3. An assumed modulo-four
qualifier clocks it only on row 0, holding that nibble across the row-1 and
row-2 `3ED` outputs, which are zero in both traces. At row 3, the previously
documented external Boolean readout combines the held nibble with live Y bits
0–2. The control clocks U12 on every raw `3ED` edge; its row-2 zero then
overwrites the row-0 nibble before row 3.

| Carrier rotation | Row-0-qualified U12 | Every-row U12 control |
| --- | ---: | ---: |
| 0° | 0/12 dibit errors | 9/12, constant output `11` |
| 45° | 10/12 dibit errors | 9/12, constant output `11` |

This pins down a **necessary clock qualification for this proposed readout**:
the all-row `3ED` gate alone cannot preserve row 0. A pictured four-bit U12
is large enough for the proposed nibble, and pictured four-bit U24 is a
plausible source of row indexing. Neither actual connection, counter clock,
reset phase nor gate pin is traced. The row-0 clock, live row-3 consumer,
previous-symbol phase storage, dibit logic, bit serialization and USART-01
RxD connection are all external hypotheses, not executed DSC instructions.

The 45° failure remains after giving the latch its required timing, so this
candidate does **not** pass C3. The next test should seek an executed or
photo-compatible phase-tracking input, or a different consumer of the
four-row outputs, then check its dibits and symbol-time output on both
streams. The missing physical wire is not a goal blocker. Full scores,
phases, event counts and source hashes are in the
[machine report](results/receiver-mask04-u12-latch-replay.json). Reproduce
from the microcode directory with
`python3 g2/receiver_mask04_u12_latch_replay.py`.

The later [matched-tail pulse replay](JOINT-MASK04-CARRYOVER-LATCH-PULSE.md)
checks this exact raw `3ED` edge schedule on a varying ADC waveform.
The row-0 qualifier retains a changed previous-sample nibble through
the next row-3 edge even after the DSC's own state rejoins; the every-row
clock control holds zero. This confirms the candidate latch's causal
delay role under the stated wiring, while the 45° decision failure
still prevents a C3 pass.
