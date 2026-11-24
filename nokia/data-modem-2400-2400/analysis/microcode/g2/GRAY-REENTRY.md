# Repeated q3 Gray-map call with controller dibits

The [single-call Gray operand test](results/gray-operand-probe/report.json)
reaches Am27S31 addresses `07C`–`07F` once under q3, then parks at 084. A
caller might invoke the routine again with retained RAM/Q and thereby create
a phase trajectory. The [reentry probe](gray_reentry_probe.py) tests that
specific possibility without treating it as recovered board control flow.

It takes four distinct USART-01 byte streams from the controller's
[uninterrupted ROM execution](MAIN-LOOP-SERIAL.md), extracts dibits in
least-significant-bit-first order, and presents each as the **hypothetical**
`D316 = 0x77 + dibit` input. This base makes the first q3 read address one of
`07C`–`07F`. After the first reset path, the probe enters PC345 once per
dibit with the previous RAM, Q and Y preserved. ROM317 reads bank zero; Y at
392 is captured as a candidate output. The PC reentry, D connection, ROM
bank and output capture are all diagnostic assumptions.

Every one of the 80 local calls completes and reads the real Am27S31 once.
The first symbol reaches `07C`–`07F`, but subsequent addresses depend on the
retained state and leave that four-entry map. By symbol 8, **all four tested
controller streams** settle into the same alternating Q values `AA/A9` and
candidate Y bytes `50/52`, despite differing dibits. Their late ROM addresses
stay near `020`–`024`. This is a two-step recurrence in the tested q3 fixture,
not a retained V.26 phase progression or a dibit-dependent output sample
stream. It excludes only this local-call and D316 bridge hypothesis; another
caller, mapping, startup state or board input path could behave differently.

The [saved report](results/gray-reentry-probe.json) records each dibit, ROM
address and byte, Q transition, output and trace digest. Reproduce with:

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/gray_reentry_probe.py
```
