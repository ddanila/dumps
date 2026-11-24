# Controller frames and line samples at the candidate D38E input

The [screen](photo_input_route_screen.py) replays two kinds of independently
generated stimuli through the same hypothetical DSC2847 D input at microcode
word 38E. The command stimulus is the four-byte frame stream emitted during
12 uninterrupted iterations of the real 8031 controller ROM, with received
selectors 00, 20, 40 or 60. The receive stimulus is 256 complementary ADC0800
codes, `127 - sample`, from the reference modem's decodable line waveform,
tested in forward and reverse order. Five current photo-constrained Am2901
mappings are run with Q=5 and zero initial RAM. The frames, ADC coding, D38E
route, ROM enable, dispatch and timing are explicit hypotheses; they are not
measured board connections.

All **30 real-PROM runs** complete and consume exactly one offered byte per
38E visit. In every run the observed four-word dispatch group and reconstructed
post-group state have exactly **one signature per current input byte**. For
the ADC stream, reversing the sample order leaves the mapping from each byte
to its signature unchanged in all five mappings. No run reads the Am27S31
after its first 38E input. The [result](results/photo-input-route-screen.json)
records output-site values, ROM-read counts, final PCs, trace digests and
source hashes.

Under this specific D38E interface and startup fixture, the tested paths do
not retain sample history or exhibit the repeated table work expected of the
receiver; sending the controller's four-byte frames there likewise does not
open a recurring ROM path. This is stronger than the earlier q3-only ADC
check, but does not exclude another physical input PC, clock phase, state
source, mapping or simultaneous command and sample traffic. The next search
should prioritize the connector and latch routes that can deliver controller
commands and ADC samples to *different* operations, rather than continuing
to treat D38E as the default ingress for both.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/photo_input_route_screen.py
```
