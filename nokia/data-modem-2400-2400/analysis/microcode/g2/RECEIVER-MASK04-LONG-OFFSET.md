# Frozen receive readout over a longer carrier-offset stream

The [adjacent-visit replay](RECEIVER-MASK04-OFFSET-VISIT-PHASE.md) found that
sampling executed `3F8` Y at visits 46/93 recovered all data dibits in two
48-symbol +7 Hz fixtures. This [longer replay](receiver_mask04_long_offset.py)
freezes that visit pair, both decision tables and their consensus, then runs
a new seeded stream with 32 `11` preamble symbols and 64 data symbols. Each
case executes 1,152,047 real-PROM words and accepts 36,000 complementary
ADC visits. The reference receiver decodes every generated PCM input before
PROM execution. At ±7 Hz, carrier phase drifts about 202° across the 96
captured symbols.

| Carrier offset | Initial phase | Wrong / measurable dibits | Unknown symbols | Unknown data |
| --- | ---: | ---: | --- | ---: |
| −7 Hz | 165° | 0 / 95 | 22, 51, 65 | 2 / 64 |
| 0 Hz | 165° | 0 / 95 | none | 0 / 64 |
| +7 Hz | 75° | 0 / 95 | 8, 22, 65 | 1 / 64 |
| +7 Hz | 165° | 0 / 95 | 50, 63 | 2 / 64 |

The longer test contradicts any claim that the frozen 46/93 readout always
produces a complete data stream at ±7 Hz. It makes no incorrect known
decisions in these cases, but five offset-case data dibits are undecided.
The zero-offset control is complete. No held-out labels were added to the
tables, and the unknowns were not filled from the reference source.

This remains conditional on the assumed complementary ADC input,
symbol-relative capture clock, external decision logic and mapping. The
tested readout is a diagnostic consumer of executed PROM state, not an
identified board circuit or verified USART-01 path. C3 stays open. Next
capture additional `3F8`/`3ED` visits around the unknown symbol positions
in continuous runs, then test a frozen phase-selection rule on fresh
offset/data fixtures and a photo-compatible latch/serial route.

The [machine report](results/receiver-mask04-long-offset.json) includes
the seed, cases, exact unknown positions, trace and source hashes. Reproduce
from the microcode directory with `python3 g2/receiver_mask04_long_offset.py`.
