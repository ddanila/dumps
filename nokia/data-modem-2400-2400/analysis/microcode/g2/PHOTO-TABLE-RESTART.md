# Repeated controller-dibit sign-table calls under a diagnostic RST pulse

The [controller-dibit route](PHOTO-TABLE-DIBITS.md) makes q1/q3 select all four
3C5/3DA sign-table entries, but its reset execution parks at `084` after a
few calls. This [bounded continuation](photo_table_restart_dibits.py) tests
whether repeated entry could turn those sign choices into an evolving signal.
It substitutes the documented 8X02 `AC=111` RST operation for the BRT at the
first 15 arrivals to `084`, preserving Am2901 RAM/Q and U9's four-entry
stack. The AC override is a **diagnostic circuit hypothesis**; no Nokia
command-override net has been traced.

The run retains the prior photo-pin, predecessor-Y dispatch and candidate
USART-01-to-D routes. For each q1/q3 mapping and scenario seed 11/14, a D=0
baseline establishes the order of reached table calls across the restarts.
The first corresponding dibits from each of the four uninterrupted 8031
line-side byte streams are then offered at `3D6` or `3C1` in that order. The
run verifies the order is unchanged, each predecessor Y equals its dibit,
and each table write follows the [exact high-byte sign formula](PHOTO-TABLE-EXACT.md).

| Scenario seed | Runs | Calls per run | Distinct source pairs per run | Distinct output pairs per run |
| ---: | ---: | ---: | ---: | ---: |
| 11 | 8 | 4 | 1 | 1 |
| 14 | 8 | 10 | 1 | 2 |

All **16 runs finish cleanly** after 2,500 microinstructions, issue 15
modeled RST pulses with balanced logical stack state, make **112** sign-table
calls in total, and end at the ordinary `084` wait. For q3, seed 14 and
controller stream `20`, the ten table entries are `3,1,2,3,3,2,3,1,3,1`.
The source pair remains `(0000,FF00)` at every call; the output alternates
only between `(0000,FFFF)` and `(0000,0001)` according to the sign entry.
No tested restart develops a progressing source pair or a carrier sample
sequence. Seed 11's four calls likewise share one source pair and one output
pair.

This is a negative result for **this** AC=RST continuation and D route, not
proof that the modem never restarts U9 or uses the sign tables for DPSK.
Upstream branch conditions and other dispatches remain scenario-driven; the
input timing, branch bus, photo-pin levels and output route are unverified.
The fixture has no Am27S31 read policy or identified DAC08 sample strobe. A
useful next candidate must update the source pair or phase from real ROM/data
before repeated sign selection and show those values reaching a sample path.

The [report](results/photo-table-restart-dibits.json) records all controller
dibits, restart cycles, table calls, source and output pairs, trace digests
and source hashes.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/photo_table_restart_dibits.py
```
