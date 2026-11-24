# U10 data-bit alternatives for the table/consumer path

The [inverted U10-bit-5 route](PHOTO-TABLE-PROMBIT-CONSUMER.md) made both
3C5/3DA sign tables and later register reads work, but the inversion is
untraced. This [source screen](photo_u10_q0_source_screen.py) tests **all eight
real U10 PROM data bits**, both direct and inverted, as candidate inputs to
U5 D0. It keeps U10's enable low for valid data and the same hypothesized
U5 Q0→Am2901 I0/A1 fan-out. The q3 mapping, four diagnostic branch seeds,
real controller selector-`20` bytes at D349 and AC=RST continuation are held
fixed. These are 64 bounded real-PROM runs, not a recovered board net.

Each polarity makes 33 reached table calls. The joint test asks whether
**every** call follows the exact high-byte sign formula, at least one
table-written register is read later, and a nonzero byte reaches an internal
consumer `140` or `146`.

| U10 D0 source class | Result in these four seeds |
| --- | --- |
| Any direct U10 data bit | No candidate meets the joint test. Bits 2 and 3 preserve all 33 table formulas, but have no downstream table-output read. |
| Inverted bits 1, 4 or 7 | Some nonzero internal reads, but not all 33 table calls match the formula. |
| **Inverted bit 5** | **33/33** table formulas, **36** downstream reads and **10** nonzero consumer visits. |

The [MMI 6381 databook](https://bitsavers.trailing-edge.com/components/mmi/_dataBooks/1978_MMI_Bipolar_LSI_Databook_1ed.pdf)
identifies O6 (dump bit 5 in this reader convention) at pin 15 and the
active-low P/E2 enable at pin 20; the 6381 variant has three-state outputs.
Those facts make a valid PROM-data experiment possible, but the databook does
not supply an inverter or identify a U10 O6→U5 D0 wire on this board. The
available photo interpretation currently favors an E2-side segment near U5
D0; it remains ambiguous. Thus bit 5 is the **best functional candidate among
this deliberately limited set**, not a physical mapping claim.

The [report](results/photo-u10-q0-source-screen.json) records all 16
source/polarity summaries, 64 trace digests and source hashes. The result
prioritizes a specific photo check or an alternative non-inverting source,
while the transmitter and receiver/echo acceptance tests remain unmet.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/photo_u10_q0_source_screen.py
```
