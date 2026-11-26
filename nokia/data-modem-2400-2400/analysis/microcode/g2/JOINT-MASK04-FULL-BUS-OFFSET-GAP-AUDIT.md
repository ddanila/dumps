# Executed receiver bytes at the four offset gaps

The [adjacent-visit screen](JOINT-MASK04-FULL-BUS-OFFSET-VISIT-SCREEN.md)
found four data dibits that no tested pair decoded correctly with the
frozen consensus tables. This audit reruns only those three failing
full-byte Tx→Rx fixtures and captures ADC input, `3F8` Y, and `3ED`
row-0/row-3 Y at the preceding, target and following symbols. The ADC
hashes and full real-PROM receiver trace digests match the prior screen.
Each receiver executes 780,047 instructions.

| Selector, offset | Symbol | `46/93` primary/alternative transition keys | `47/94` primary/alternative result | Other tested result |
| --- | ---: | --- | --- | --- |
| Call −7 Hz | 46 | `F1`/`E3`, both unknown | `0` / `2` (conflict) | No correct consensus |
| Call −7 Hz | 56 | `49`/`1A`, both unknown | unknown / unknown | `47/93` says `0`; `94/141` says `1` |
| Call +7 Hz | 56 | `71`/`62`, both unknown | unknown / unknown | `94/141` says `3` |
| Answer +7 Hz | 39 | `0E`/`1C`, both unknown | `0` / `2` (conflict) | `47/93` says `0` |

The expected dibit happens to be `2` in all four selected gaps; that is
an observation about these two payloads, not a proposed recovery rule.
At call −7 symbol 46 and answer +7 symbol 39, the alternative `47/94`
table contains the correct label, but the independently frozen primary
table says `0`, so the conservative consensus abstains. At the two symbol
56 gaps, no tested pair yields a correct known consensus. These are two
different issues: feature conflict and missing or misleading transition
coverage. Filling unknowns from a single adjacent pair cannot solve both.

The [machine report](results/joint-mask04-full-bus-offset-gap-audit.json)
contains the full nearby executed bytes and ADC sample indices. For
example, call −7 symbol 46 has `3F8` Y `7F` at visit 46, `1F` at 47/93,
and `5F` at 94; answer +7 symbol 39 has `8F`, `DF` and `AF` at those
visits. The `3ED` row bytes also change. Thus the PROM run retains
signal-dependent observations at these sites; the failure belongs to the
current external feature/decision hypothesis under this fixture. This
does not prove that a Nokia decision circuit used these bytes or that
another PROM output necessarily carries the correct bits.

Next, test a phase-aware decision that uses the executed row outputs or
additional samples, with conflict handling specified before a fresh
payload and phase-start holdout. Also try a separately labelled ADC or
clock route if the readout remains ambiguous. Keep C3 open and G2 active.

Run `python3 g2/joint_mask04_full_bus_offset_gap_audit.py` from the
microcode directory.
