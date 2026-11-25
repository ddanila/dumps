# Controller D-byte lane changes the result

The [upper-address screen](INDEPENDENT-SLICE-ADDRESSES.md) had a false-negative
input fixture: it supplied each controller bit as byte `00` or `01`. At
`38E` in the separated instruction layout, the lower U2 slice does not use D.
The upper U8 slice does, after the candidate U8 I4←U2 I1 and I6←U2 I2
links, but it sees **D7–D4**, so `00` and `01` are indistinguishable there.
The earlier conclusion is now restricted to that D0 placement.

The [reproducible screen](independent_slice_d_lanes.py) keeps the hypothetical
upper B-address field from the `b` variant and places the same 128 controller
bits on each D-byte lane in turn. It compares all-zero, all-one, actual
controller bits and a one-bit pulse at input visit 20. Each 1,580-cycle run
reaches 128 D38E inputs and 128 visits each to candidate output words `39E`
and `39F`.

| Bit lane used for controller data | `39E` after startup, zero / one | Pulse effect at `39E` |
| --- | --- | --- |
| D0–D3 | `1B` / `1B` | None |
| D4 | `1B` / `3B` | Output visit 21 only |
| D5 | `1B` / `5B` | Output visit 21 only |
| D6 | `1B` / `9B` | Output visit 21 only |
| D7 | `1B` / `1B` | None at this site |

For D4–D6, the actual controller stream matches the one-loop-delay rule at
all 127 output visits after startup: `Y39E[k] = 1B + (bit[k−1] << (lane+1))`.
The first `39E` value is `FB` in every run, independent of the first input.
`39F` stays `EC` in all eight lane cases. D7 changes internal state trace
without changing either candidate output site in this fixture. All selected
ROM reads after the first input still use one address per run.

This is a real input-to-ALU dependency **under the stated field and bus
hypotheses**, and it corrects the D0-only false negative. Its one-visit pulse
response looks like delayed bit forwarding, not the multi-sample carrier or
persistent phase state required by the transmitter test. Neither `39E` nor
`39F` is yet tied to the photographed DAC latch or clock. The controller-to-D
route and bit lane are untraced, so this is a candidate computation rather
than a claim about physical line output.

The [report](results/independent-slice-d-lanes.json) records the input and
output comparisons, pulse positions, trace digests, ROM addresses and source
hashes.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/independent_slice_d_lanes.py
```
