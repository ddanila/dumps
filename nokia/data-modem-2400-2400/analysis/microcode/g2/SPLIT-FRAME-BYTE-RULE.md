# A conditional byte-field relay in the 389–3A1 loop

Under the [separated-slice instruction](INDEPENDENT-SLICE-FIELDS.md) and
**untraced** U18 bits 1–4 upper-B field, the real-PROM loop has an exact
input/output rule. Number D38E visits and `39E` visits from zero within the
recurring loop. After the startup output `FB`, the executed ALU Y value is:

`Y39E[n] = 0x1B + 2 × (D38E[n−1] & 0x70)` for `n ≥ 1`.

Thus the loop relays only the previous byte's bits 4–6 into output bits 5–7,
with a fixed low pattern. Bits 0–3 and 7 do not affect this candidate output
in the tested fixture. This extends the [one-bit D-lane result](INDEPENDENT-SLICE-D-LANES.md)
to complete bytes.

The [execution check](split_frame_byte_rule.py) feeds all 256 byte values in
ascending order and again in descending order, then replays four 48-byte
frame streams from the unchanged 8031 main-loop run. Every one of the **704
output visits** matches the formula, including six startup values. Across
the two exhaustive sweeps, every possible input byte is paired with its
next-visit output. All six runs select 256 or 48 input bytes as offered and
continue to read only Am27S31 address `1F6` after the first input. For the
controller's initial frame `80 02 A1 7A`, the candidate outputs begin
`FB 1B 1B 5B`; the rule predicts the same values from the preceding bytes.

This is a byte-field extraction and one-loop delay in **this emulator
scenario**, rather than a retained phase or filter computation. If ALU Y
fed the LS273 D byte in order at `39E`, the one photo-supported DAC bit
B5←Q4 would stay one for all 256 post-startup input values. The
[eight-hold latch replay](SPLIT-DAC-CLOCK-SCREEN.md) separately shows that
the `38E` and `39E` direct-clock scenarios yield constant codes under
constant symbols. The physical controller-to-D bus, upper B field, latch
data order and clock are not recovered. In particular, the
[upper photo-bundle screen](PHOTO-UPPER-BUNDLE.md) found that 24 tested
high-bit upper-B orders hold `39E` fixed; it does not validate this low-bit
field.
The [instruction-field screens](UPPER-I-FIELD-SENSITIVITY.md) show that this
relay also depends on an unverified U18.6 fan-out to both U8 I2 and I7.
Changing the lower U2 I2 source can preserve the relay while extending its
internal transient to four loop checkpoints
([lower-field result](LOWER-I-INPUT-PIPELINE.md)); neither result establishes
the physical wiring or a modem waveform.

The [report](results/split-frame-byte-rule.json) records all 256 byte
results, controller frame witnesses, ROM address, trace digests, source
hashes and explicit assumptions.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/split_frame_byte_rule.py
```
