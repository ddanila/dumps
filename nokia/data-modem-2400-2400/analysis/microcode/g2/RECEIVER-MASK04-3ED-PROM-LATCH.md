# A PROM decode can clock mask-04 R1/Y after every receive row

The [mask-04 arithmetic trace](JOINT-MASK04-ADC-ROM-WRAPPER-RULE.md)
shows that `3ED` puts pre-word R1 on Y, and that ADC changes that byte.
This experiment tests a labelled, photo-compatible way to capture it.
The [annotated board photo](../board/evidence/front-annotated.jpg) shows
U19 (`SN74LS10N`, a three-input NAND) near U12 (`SN74LS175N`, a four-bit
flip-flop). Their actual pin connections are untraced. U12 could hold
R1's low nibble if it received Y[3:0] and the proposed U19 clock; the
scenario does **not** assume that this is proven Nokia wiring.

An exhaustive search of the first 200 executed raw-PROM words finds no
one- or two-literal decode that is high only at `3ED`. There are 54
three-literal decodes, but exactly one needs no inverted PROM bit:

```text
U11.D7 & U17.D3 & U18.D5
```

With those three levels feeding a NAND, the candidate clock rises when
the decode falls. Eleven independent 192,047-instruction real-PROM
streams test the full schedule under the mask-`04` field map, four-row
dispatch and inverted previous-overflow TEST. Each selects 6,000
complementary ADC bytes. The AND is high **only** at `3ED`, 24,000 times
per stream, and the NAND rises only on `3ED→3EA`, also 24,000 times.
The byte present on Y just before each edge equals R1 in all cases.
Those captures have 10 or 11 distinct byte values across the streams.

The captured stream has four row bytes per ADC-table visit, including
three phases missed by the earlier [after-`3FE` R1 screen](RECEIVER-MASK04-RETAINED-BIT.md).
At all 1,500 capture phases per symbol, the screen tries each Y bit,
both direct and previous-symbol-XOR interpretations, target dibit bits,
lags −2…+2 and a training-selected polarity. None of 240,000 choices
fits all 36 training bits. The training-selected best is Y bit 1,
direct, at phase 568 and lag +1: 6/36 training errors, 5/48 holdout
errors and 12/48 errors on four fresh streams. It does not establish
serial receive output.

The NAND inputs, Y-to-U12 data pins, setup phase and any U12-to-USART 01
RxD route remain hypotheses. The direct-bit failure rules out this simple
readout under the tested fixture, not a multi-byte or adaptive receiver.
C3 stays open. The next test should use the four captured row nibbles as
a stateful decision candidate or find an executed consumer beyond the
latched byte; missing continuity does not block that experiment.

The [machine report](results/receiver-mask04-3ed-prom-latch.json) records
the gate search, full-trace edge counts, captured-byte hashes, bit scores,
fresh-stream validation and source/photo hashes. Reproduce with
`python3 g2/receiver_mask04_3ed_prom_latch.py` from the microcode
directory.
