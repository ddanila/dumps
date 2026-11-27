# The frozen receive gate depends on the assumed mode boundary

The [revised package-capacity gate](JOINT-MASK04-12A-TWO-BIT-PACKAGE-ROUTE.md)
passed carrier-`165/167` payloads at both 1.0× and 1.15× receive gain.
Those runs offered an assumed `81→A1` controller byte at DSC read `3EB`
near symbol 32. This control keeps the **same transmitter payloads,
carrier starts, PCM samples and PC path** at 1.0× gain while changing
only that imposed `3EB` sequence:

| Assumed `3EB` schedule | Wrong dibits across call/answer at carrier `165` | Wrong dibits across call/answer at carrier `167` | Payloads |
| --- | ---: | ---: | --- |
| `81→A1` near symbol 32 | 0 / 0 | 0 / 0 | All exact |
| Held `81` throughout | 8 / 10 | 11 / 13 | All wrong |
| `81→A1` near symbol 48 | 4 / 4 | 4 / 6 | All wrong |

For every matched trio, Tx and PCM hashes agree, the executed PC-path
hash agrees, and the full receiver trace changes. No modeled ADC sample
clips. Every wrong transition touches captured nine-bit state `01C`;
held-`81` errors begin after symbol 32, and the late-edge errors are
confined to symbols 32–48. Moving the mode edge therefore moves the
failure interval. The controller's USART status-error counter remains
zero even when all eight decoded bytes are wrong; payload equality is
checked separately.

Across all 58 saved real-PROM streams, the nine-bit phase graph now has
**102 directed conflicts**. Adding the imposed `3EB` mode bit 5 gives
one 54-state component with **zero conflicts**. State `01C` requires
different relative phases when that bit is low and high. This is a
discriminating *logical* mode-input result, not proof that `3EB` bit 5
is wired to the physical decision gate.

An 80-bit screen of the already captured Y and row values finds 24
single-bit additions with zero conflicts. One concrete alternative is
first `3F8` Y4 at visit `46`: the resulting 10-bit graph has one
48-state component and zero conflicts. It separates the conflicting
`01C` cases without a direct mode input to the gate. A storage-capacity
hypothesis can use U14's spare first-capture latch to hold Y4, then U12's
fourth flip-flop to copy it at visit `47` before U14 is reused for later
Y4 at visit `94`. Row-0 Y0/Y1 remain unchanged across visits `46→47`
in all 3,770 symbols. First and later Y4 differ in 2,046 symbols, so
they cannot simply be treated as the same retained bit. The gate logic
for this 10-bit route has **not** been realized in the photographed
package budget, and the feature was selected on these failure streams.

The [mode audit](results/joint-mask04-12a-two-bit-package-mode-audit.json)
records matched trace hashes, every error index, both phase graphs,
the 80-bit screen and source hashes. Reproduce the real-PROM controls
with `joint_mask04_12a_two_bit_package_mode81.py` and
`joint_mask04_12a_two_bit_package_mode_late48.py`; run
`joint_mask04_12a_two_bit_package_mode_audit.py` on their captures.

The frozen nine-bit circuit is validated for the tested `81→A1`
schedule and gains, but fails these alternate schedules. Next freeze a
mode-qualified or first-Y4 capture/gate candidate and challenge new
payloads. Keep C3/G2 active; the photographed mode, latch and USART
nets remain testable assumptions.
