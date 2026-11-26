# An independent `3F9` feature fits training but leaves holdout gaps

The [ROM-sensitive loopback gap audit](JOINT-MASK04-12A-READOUT-GAP-AUDIT.md)
found four data dibits where every previously frozen capture pair is
unknown. This [feature screen](receiver_mask04_3f9_3fa_feature_screen.py)
therefore captures executed `3F9` and `3FA` Y at three predeclared
symbol-visit pairs: `46/93`, `47/94` and `94/141`. It tests each of
the four two-bit slices of `3F9` Y, with no extra bit or one `3FA` Y0
bit, as a previous/current-symbol transition key. There are 36
candidate features. The lookup and symbol clock are external diagnostics.

Six independent legal 16-dibit carrier streams at 45° and 135° each
execute 192,047 real-PROM words. The four streams shared with the
earlier carrier-phase run reproduce its trace and ADC hashes. Across
these inputs, `3F9` Y takes 14–15 values and `3FA` Y takes only `20`
or `21`.

The first seed at both rotations trains the features; two new seeds
at both rotations are holdout. Fourteen candidates make all 24
training decisions without a conflicting or unknown key. The selected
candidate, chosen from training only and preferring no unnecessary
`3FA` bit, uses **`3F9` Y bits 4–5 at visits 46 and 93**. Its frozen
16-key transition table scores:

| Set | Wrong | Unknown | Dibits |
| --- | ---: | ---: | ---: |
| Independent training | 0 | 0 | 24 |
| Independent holdout | 0 | 16 | 48 |

This identifies another information-bearing executed output, but it
does not establish a general receiver or a board decision circuit.
Unknown transition keys remain unknown, and the output latch, symbol
clock and USART RxD route are untraced. The table is frozen for the
separate [buffered-line gap test](JOINT-MASK04-12A-3F9-GAP-TEST.md).

The [machine report](results/receiver-mask04-3f9-3fa-feature-screen.json)
contains all six trace/input/output hashes, 36 feature scores and the
frozen lookup. Reproduce with
`python3 g2/receiver_mask04_3f9_3fa_feature_screen.py`.
