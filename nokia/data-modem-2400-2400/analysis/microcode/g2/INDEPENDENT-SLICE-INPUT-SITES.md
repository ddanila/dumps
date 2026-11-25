# Selected D-input sites in the independent-slice loop

The [independent-slice layouts](INDEPENDENT-SLICE-FIELDS.md) change which
microinstructions actually select the external D byte. A visit to a D input
site is not evidence that the ALU consumed the offered byte. In particular,
the reversed-upper layout visits D38E 128 times but neither slice selects D
there; the earlier report called those bytes "consumed" too loosely. The
corrected report distinguishes bytes advanced by the scenario from bytes
selected by the executed instruction.

The [site screen](independent_slice_input_sites.py) finds every D-selected
word in the recurring `389`–`3A1` loop after the first D38E visit. At each
site it compares a constant-zero D stream with 128 reference line-sample
bytes, forward and reverse, in both candidate ADC0800 bus polarities. A
single `FF` impulse at visit 20 tests whether a difference survives into a
later iteration. The full modeled RAM, Q, previous Y, flags, stack and next
PC are compared after each `3A1` boundary. These site assignments, sample
schedule and PROM-to-slice fields remain hypotheses.

| Layout | Actually selected D sites | Reference-sample boundary differences | One-sample impulse |
| --- | --- | --- | --- |
| Separated pairs | `38C`, `38D`, `38E` | `38C`/`38D`: 0; `38E`: 108/128 | Only boundary 20 differs at `38E` |
| Separated, reversed upper | `38B`, `38C`, `38D`, `39F`, `3A1` | First four: 0; `3A1`: 110/128 | Only boundary 20 differs at `3A1` |

The inverted-bus and reversed-order runs have the same zero/nonzero site
classification. No tested site changes any reached candidate output ALU Y
event at `392`–`39F`. The `38E` test replaces the controller-bit stream with
ADC-like bytes at that word, so its boundary effect is not simultaneous Tx/Rx
operation. In the reversed-upper layout, D38E is not selected even when real
controller bits are offered there.

The impulse result is the decisive history check in this fixture: the only
two sites that change a loop-boundary state converge again at the very next
boundary. Neither supplies the persistent phase/filter state, changing DAC
samples or recovered USART bits required by G2. This is a scoped result for
the tested q3 branch, initial Q=5 and two hypothetical instruction layouts;
other paths, states and physical input routes remain open.

The [report](results/independent-slice-input-sites.json) records each site,
executed low/high source code, selected visits, all waveform comparisons,
impulse index, output comparison, trace digests and source hashes.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/independent_slice_input_sites.py
```
