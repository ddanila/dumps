# A simultaneous D3A1 byte reaches R7 for one loop boundary

The [lower instruction alternatives](LOWER-I-INPUT-PIPELINE.md) make `3A1`
select external D under U2 I2←U11.0 or U11.4. That creates a candidate
second ingress while controller bits continue at D4 of `38E`. The
[dual-input screen](dual_input_adc_nibble.py) runs the real four control
PROMs and Am27S31 dump with both sources scheduled at once. It offers each
of the **256 byte values** at the 21st `3A1` visit, with zero at all other
`3A1` visits; the unchanged 128-bit 8031 scrambler fixture remains at
`38E`. The D3A1 route, D38E route, U11 source and clock are labelled
hypotheses, not measured board wiring.

For both U11 source choices, 23 D3A1 visits and 23 D38E visits occur and
actually select their offered bytes in the 320-microinstruction window.
At `3A1` visit 20, R7 follows this exact executed rule for **all 256**
offered bytes:

`R7 = 0x60 | ((0x0B + (D3A1 & 0x0F)) & 0x0F)`.

The upper four input bits have no effect on this R7 value. For example,
`00→6B`, `01→6C`, `05→60`, `0F→6A`, and `FF→6A`. This is an 8-bit input
being reduced to a four-bit addition in the modeled lower slice; it is not
a recovered ADC conversion rule.

At the **next** `3A1` boundary, R7 is `7B` for every tested byte and the
full modeled RAM/Q/flags/stack/next-PC state matches the zero-byte run.
The PC path, selected ROM addresses and all reached candidate output ALU
events at `392–39F` also match the zero-byte control in every run. Thus this
particular simultaneous input route computes a one-boundary transient, not
a retained receive filter, decoded bit or line-output modulation. The
[report](results/dual-input-adc-nibble.json) contains the exhaustive rule
check, example bytes, observation digests and source hashes.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/dual_input_adc_nibble.py
```
