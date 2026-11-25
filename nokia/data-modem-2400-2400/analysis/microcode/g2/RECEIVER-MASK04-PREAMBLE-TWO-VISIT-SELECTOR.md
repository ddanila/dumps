# A second executed preamble visit resolves the 45°/180° alias on the phase grid

The [phase-47 alias](RECEIVER-MASK04-PREAMBLE-PHASE-ALIAS.md) showed that
the two available external receive readouts need different selection at
45° and 180°, but their entire 32-symbol preamble looks identical in
`3ED` row-0/row-3 Y and `3F8` Y at ADC visit 47. The
[all-visit replay](receiver_mask04_preamble_visit_screen.py) re-executes
the two matched 576,047-instruction real-PROM traces and matches their
earlier trace/ADC hashes. In the steady preamble symbols 8–27, 281 of
375 ADC visits differ at `3F8` Y, 234 at `3ED` row-0 Y and 281 at
`3ED` row-3 Y. Visit 47 still aliases exactly. At **visit 94**, executed
`3F8` Y is consistently `2F` at 45° and `BF` at 180°; Y7 separates them.
The [visit-94 one-bit test](receiver_mask04_visit94_selector.py) freezes
“Y7 high → nominal; low → diagonal” and replays six other grid rotations.
It resolves the 45°/180° pair but fails at 0°/90° (15/16 unknown) and
225° (14/16 wrong). One bit is not a general phase-class selector.

The [combined selector](receiver_mask04_grid_preamble_selector.py) uses
the row-0 `3ED` Y byte at visit 47 and `3F8` Y7 at visit 94, both from
preamble symbol 16:

```text
row0 = FD or F2                  -> nominal readout
row0 = F5 and visit94.Y7 = 1     -> nominal readout
row0 = F5 and visit94.Y7 = 0     -> diagonal readout
row0 = F3                        -> diagonal readout
other values                     -> unknown
```

This rule was fixed using the earlier eight-angle `0x72A1` stream. On a
**new** `0xB812` data stream, each angle executes 576,047 real-PROM
instructions continuously from the 32-symbol `11` preamble through 16
data symbols. The rule selects the intended external readout before data
starts:

| Carrier angle | Preamble row-0 Y / visit-94 Y | Readout | Data errors / unknown |
| ---: | --- | --- | ---: |
| 0° | `FD` / `3F` | nominal | 0 / 0 |
| 45° | `F5` / `2F` | diagonal | 0 / 0 |
| 90° | `F2` / `3F` | nominal | 0 / 0 |
| 135° | `F3` / `7F` | diagonal | 0 / 0 |
| 180° | `F5` / `BF` | nominal | 0 / 0 |
| 225° | `F3` / `DF` | diagonal | 0 / 0 |
| 270° | `F2` / `BF` | nominal | 0 / 0 |
| 315° | `F5` / `7F` | diagonal | 0 / 0 |

The selected readout recovers **248/248 measurable preamble dibits** as
`11` and **128/128 data dibits** with no unknowns. These are eight phase
rotations of one fresh data stream, not eight independent data streams.
The [intermediate-angle challenge](receiver_mask04_grid_selector_between.py)
applies the frozen rule to eight earlier full-PROM captures at 15°–165°:
three angles have no selected rule, and **none** produces complete correct
data. The two-visit result is therefore a conditional *grid* decoder,
not arbitrary carrier tracking.

The [visit-screen report](results/receiver-mask04-preamble-visit-screen.json),
[one-bit report](results/receiver-mask04-visit94-selector.json),
[grid-validation report](results/receiver-mask04-grid-preamble-selector.json)
and [intermediate challenge](results/receiver-mask04-grid-selector-between.json)
retain trace/source hashes, observed bytes and scores. The `3F8` gate,
row-0 latch, symbol counter, selector/phase logic, bit serialization,
RxC/SYNDET and physical USART RxD route are still hypotheses. The
input is an assumed complementary ADC encoding of a reference waveform.
C3 remains open. The next receiver experiment should find a generalizing
executed phase adjustment or multi-visit decision across intermediate
angles and carry it into the paced USART handoff.
