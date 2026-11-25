# D3F8 input changes later ROM reads and a branch under the data-bit mapping

The [read-valid PROM-data source candidate](LOWER-I-PROM-DATA-ROUTE.md)
reaches a repeated `3ED–3FA` loop. The [input screen](lower_i_d3f8_input.py)
uses that same real-PROM mapping (I7/A0 from inverted U10 D6, I0/A1 from
U11 D2, lower I6 from U11 D0), Q=5 and zero initial RAM. It offers explicit
bytes at the three repeated, actually selected external D sites. The source
of those D bits and the latch/sample clock are **untraced hypotheses**.

With D3F8 held at its fixture default `01`, 1,580 microinstructions make
**192 selected D3F8 visits** and **386 selected ROM reads**. Holding D1, D2
or D3 high while keeping D0 high preserves all 192 loop visits but changes
350–367 selected ROM-address events and many ALU Y values. This is more than
a one-word bit relay under this mapping, though it is not a modem function
identification.

| One changed D3F8 byte at visit 20 | Boundaries different from `01` control | First PC divergence | D3F8 visits before exit |
| --- | --- | ---: | ---: |
| `03` (D1) | 20–30 | 291 | 31 |
| `05` (D2) | 20–24 | 243 | 25 |
| `09` (D3) | 20–33 | 315 | 34 |

All three pulses change selected ROM addresses before the paths diverge.
Offering the actual 128-bit 8031 scrambler stream on one of those lanes
(with D0 still high) exits after 28, 38 or 53 D3F8 visits, respectively.
The stimulus is selected and has a sustained internal effect, but these
exits do **not** meet the transmitter test: the run does not consume the full
controller stream or produce a traced DAC sample sequence.

The other selected sites separate the input roles in this fixture. Offering
the controller stream on D1 of D3FA changes 121 D3FA ALU Y events but no
selected ROM address or PC path. Toggling each D0–D7 bit separately at D3EB
leaves its full trace digest unchanged. These are scoped controls, not pin
assignments for the physical board.

The [machine report](results/lower-i-d3f8-input.json) records the impulse
boundary and ROM differences, constant-bit and controller streams, selected
site counts, trace digests and source hashes. The next receiver/transmitter
discriminator is a photo-compatible source and clock for D3F8 plus a sustained
route from the resulting state to a bit decision or DAC-bound sample.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/lower_i_d3f8_input.py
```
