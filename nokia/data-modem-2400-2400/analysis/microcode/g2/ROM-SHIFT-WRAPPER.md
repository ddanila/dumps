# Real-ROM input releases the reset-driven shift wrapper

*Diagnostic execution under the fitted-original mapping; not recovered board wiring.*

The [constant-D reset study](../assumed/DRAIN-RESET.md) reaches the wrapper at
150 under seeded dispatch, but 255 of 256 held input bytes repeat in its shift
loops. This experiment substitutes bytes from the actual Am27S31 dump at
D-consuming PCs chosen by a three-term diagnostic ROM-enable fit. The ROM
address is the preceding ALU Y plus a fixed bank offset, both explicit
scenario hypotheses. The seed selects the same reset path as the prior study.

Gate fit 61 selects 69 PCs, including 299 and 187. Across **all 256 held D
bytes, both ROM banks and dispatch seeds 6 and 14** (1,024 runs), every run
visits 299 and 187, returns through 24E, and ends the 1,000-cycle window in
the wait at 084. All runs are error-free in the executor; none visits the
candidate output word 392. Thus real ROM data can release the wrapper under
this explicit read policy, but it does not establish an oscillator or modem
signal.

The upper-bank D=80 witness makes the mechanism visible. At 299, Q follows
`80,40,20,10,08,04,02,01,00` (hex); the ROM addresses are `180,140,120,
110,108,104,102,101,100`. The corresponding ROM bytes change, then reach
`ROM[100]=00`. The second 299 call also shifts Q to zero. Both visits to 187
then read `ROM[100]=00` with Q=00, so the left-shift loop exits. In the lower
bank the corresponding base byte `ROM[000]` is also zero. The observed 187
exit therefore depends on a zero table entry and a finite Q drain, not on
retained modulation state.

All **12** fitted three-term gates selecting 187 were also screened at held
D=`00,01,40,80,FF` in both banks (120 cases). Ten gates give the same wrapper
exit for those samples. Fits 99 and 102 instead park at 117 for `40,80,FF`
before reaching the wrapper; their wider read selection changes earlier
control flow. That sensitivity is preserved in the [report](results/rom-shift-wrapper/report.json),
not hidden by selecting the favorable gate.

Reproduce with:

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/rom_shift_wrapper.py
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode/g2 -p 'test_rom_shift_wrapper.py'
```

The saved [witness trace](results/rom-shift-wrapper/witness-trace.jsonl) and
[scenario](results/rom-shift-wrapper/witness-scenario.json) specify the inputs;
the report includes source hashes and every sweep outcome. Dispatch remains
seeded random, D is a constant diagnostic stub outside the selected read PCs,
and the ROM enable/address wiring is untraced. No 8031 command or bitstream,
line-output converter, ADC sample path, or echo state participates. The next
test must find a reached, controller-dependent ROM/address recurrence or
another path that retains and emits a changing signal.
