# No fixed-phase dibit decision in the interleaved receiver state or flags

The [two-row `3EC` dispatch hypothesis](RECEIVER-DISPATCH-SOURCE.md#a-two-row-index-schedule-survives)
sustains reference ADC samples and changes real Am27S31 lookup addresses.
These [state-byte](receiver_two_row_decision_screen.py) and
[ALU-flag](receiver_two_row_flag_screen.py) screens test whether that path
already exposes a dibit decision. Both execute the same joint upper-source
field map with `3EC` entries alternating `0,2`, complementary ADC bytes held
`94,94,94,93` visits per four samples, and the real control PROMs. Each of
seven independent streams completes **12,000 `D3F8` visits** in 192,047
microinstructions; the reference receiver recovers the supplied dibits.

Training uses two periodic and one seeded nonperiodic stream (36 symbol
checks); a separate periodic and three other nonperiodic streams supply 48
holdout checks. Symbols 2–13, all **750 ADC-visit phases** per symbol, lags
−2…+2 and both polarities are tested. State bytes are Y at `3F8–3FA`, Q and
RAM 0–15 after `3FA`. The flag screen also checks carry, overflow, sign and
zero at each of the eight executed words in table rows `3EF–3F2` and
`3F7–3FA`; the first row's flags are held until the next `3FA` visit.

| Readout family | Minimum training errors, dibit bit 0 / 1 | Exact training fits |
| --- | ---: | ---: |
| One direct state-byte bit | 5 / 5 | 0 |
| State-byte bit XOR previous symbol | 5 / 4 | 0 |
| State-byte difference from previous symbol | 3 / 6 | 0 |
| One ALU flag | 8 / 8 | 0 |

The nearest state-bit result is Q bit 4, subtracted from the previous
symbol at visit phase 110 with lag +1. It has **3/36** training errors and
**27/48** holdout errors. Twelve of the 32 flag sites vary under these
stimuli; none gives a close direct decision. A further codebook screen maps
one state byte, its XOR, or its modulo-256 difference from the previous
symbol to a dibit, allowing up to 4, 8 or 16 code values. None of these
families fits the training set exactly; the best reported 16-value case with
at most four training errors has 3/36 training and 42/48
holdout errors, with six unseen holdout codes.

The [state report](results/receiver-two-row-decision-screen.json) and
[flag report](results/receiver-two-row-flag-screen.json) retain per-family
counts, train/holdout split, all stimulus digests and source hashes. This
excludes only **single-site, fixed-phase** readouts in the declared two-row
fixture. It does not rule out a multi-sample filter/decision, a different
dispatch schedule, or a separately clocked output latch. Neither an
internal decision nor a path to USART RxD is established; C3 remains open.

Reproduce with:

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/receiver_two_row_decision_screen.py
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/receiver_two_row_flag_screen.py
```
