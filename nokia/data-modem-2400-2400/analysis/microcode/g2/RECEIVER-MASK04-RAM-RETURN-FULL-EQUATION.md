# The complete `3FA` Y byte is a delayed code plus a current-sample bit

The [full-byte replay](receiver_mask04_ram_return_full_equation.py)
hash-matches both legal-carrier delayed-RAM feedback runs and their
same-input write-only controls. It combines the already verified
[three-sample high-nibble delay](RECEIVER-MASK04-RAM-RETURN-DELAY-EQUATION.md)
with the independently executed
[`3FA` current-ADC codebook](JOINT-MASK04-RECEIVE-3F9-3FA-CODEBOOK.md).
The codebook's low bit is one exactly for current complementary ADC
high nibbles `6`, `B` and `C`.

For each held ADC sample `s`, every executed `3FA` Y byte in the feedback
fixture obeys:

```text
high = ((Y3F9_high[s − 3] + 0x20) & 0xF0)  # 0x20 for the first three samples
low  = 1 if ADC_high[s] is 6, B or C else 0
Y3FA = high | low
```

This predicts **12,000/12,000 full Y bytes** across two real-PROM
carrier runs. The feedback and write-only controls have identical low
bits at every visit, and both low-bit streams match the independent
current-ADC codebook without exception. The two runs together cover
all sixteen current ADC high nibbles.

The conditional external-memory route therefore exposes a fixed
three-sample code and a current-sample class bit at `3FA`. It has not
produced an onboard differential decision or adaptive echo residual.
This is a result about the declared RAM mux, TEST and ADC fixture; other
modes, return timing, output latches and serial circuits remain open.
Next inspect an executed output that consumes a varying trained
coefficient, or test a separately clocked decision/USART route on fresh
legal data. C3/C4/G2 remain active without waiting for pin continuity.

The [machine report](results/receiver-mask04-ram-return-full-equation.json)
records trace matches, nibble coverage and zero equation mismatches.
Reproduce with `python3 g2/receiver_mask04_ram_return_full_equation.py`.
