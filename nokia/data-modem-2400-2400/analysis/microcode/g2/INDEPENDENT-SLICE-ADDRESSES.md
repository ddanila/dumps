# Independent upper-slice register-address candidates

The [instruction-field screen](INDEPENDENT-SLICE-FIELDS.md) allowed U8 to
decode a different instruction from U2, but both slices still used the same A
and B register addresses. That coupling is not established by the board
photographs. The emulator now accepts provenance-labelled `a_high` and
`b_high` fields, and the [screen](independent_slice_addresses.py) runs four
variants of the separated-pair instruction layout with the real PROMs:

| Variant | U8 A field | U8 B field |
| --- | --- | --- |
| `none` | U2 A field | U2 B field |
| `a` | `18.1, 18.0, 17.7, 17.6` | U2 B field |
| `b` | U2 A field | `18.4, 18.3, 18.2, 18.1` |
| `ab` | Both independent fields above | Both independent fields above |

The A variant tests a mirrored U17→U29→U8 route for the upper A bits. The B
variant tests a U18→U30→U8 bundle. These are **wiring assumptions** suggested
by component placement, not pin-level traces; the bit order remains unknown.
The U2 fields and U8 I4/I6 crosslinks retain their earlier hypotheses.

All four Q=5 variants complete 1,580 cycles with 128 D38E visits that select
the offered D byte and 127 selected ROM reads after the first input. Only
changing U8 B changes reached candidate output values: `b` gives `39E=FB`
once, then `1B`, and `39F=EC`; `ab` gives `39E=0B`, `39F=FB` throughout.
The `none` and `a` variants hold `0B` at both sites. The single `FB` in `b`
is a startup transient, not a changing waveform.

Real controller bits, 128 zero bits and 128 one bits give identical modeled
state traces within each Q=5 variant. For `b` and `ab`, the screen also tests
all 256 startup Q bytes for 512 cycles, then compares zero and one streams in
1,580-cycle runs for each seed reaching both D38E and `39E`: **24 seeds** for
`b`, **16** for `ab`. Every such run selects all 128 offered input bytes; none
has a different trace or candidate output set between zero and one. Thus
independent upper register addresses do change computation under these field
assumptions, but they do not connect this controller bitstream to a changing
output in the tested loop. The ROM address after input remains fixed within
each Q=5 variant.

The [report](results/independent-slice-addresses.json) records the complete
field choices, seed lists, selected-input counts, output sets, trace digests
and source hashes. The next useful test is a different input route or
instruction/clock mapping, or a controller state that reaches another loop;
the upper latch pin order and DAC clock remain untraced. No transmitter or
receiver acceptance check is met by this screen.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/independent_slice_addresses.py
```
