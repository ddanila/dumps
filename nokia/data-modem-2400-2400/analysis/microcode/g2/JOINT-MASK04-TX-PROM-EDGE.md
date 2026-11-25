# The candidate DAC strobe also runs on the joint receive/transmit map

The earlier [divided raw-PROM DAC clock](PHOTO-TX-DIVIDED-PROM-CLOCK.md)
was checked on the q3 transmitter map. The
[joint-map replay](joint_mask04_tx_prom_edge.py) applies the same explicit
U10 D2 clock hypothesis to the fixed lower-mask-`04` map used for the
continuous receive experiments. It uses the same actual 8031 A1–A4
stimulus and two selector modes, then compares each new full-PROM trace
with the independently saved [joint-map transmitter run](JOINT-FOUR-ROW-RETENTION-TX.md).

Both 1,248,256-instruction runs match their prior joint-map trace digests.
Each executes 312,054 U10 D2 rises at `129` and falls at `12A`. A labelled
375-edge counter selects 832 samples exactly 1,500 microinstructions
apart. Capturing the byte before a rise (`128` Y) or before a fall
(`129` Y) gives two candidate 74LS273 clock phases. The falling-edge
raw-byte SHA-256 equals the saved joint-map `Y129` sample hash in each
mode, so this is the same executed byte stream with a concrete raw-PROM
edge schedule.

| Joint mask-`04` result, six surviving DAC bus orders | Selector `40` | Selector `60` |
| --- | ---: | ---: |
| A1 peak, either latch phase | 2,100 Hz | 2,100 Hz |
| A3/A4 matched-filter errors, each phase across six buses | 0/372 | 0/372 |
| Late-A1 tone fit R², either phase | 0.9275–0.9278 | 0.9275–0.9278 |
| A3/A4 reference-shape fit R², either phase | 0.8336–0.8381 | 0.8104–0.8149 |

The two raw-byte streams are **not identical**: all 832 samples differ
in each mode, with a mean absolute difference of 10.769 byte counts and
a maximum of 12. Their tested filtered metrics nevertheless coincide to
the report's precision. Neither selected-bus byte hash matches the
earlier q3 edge replay. Thus the q3 result's tone-versus-pulse-shape
preference between the two latch phases cannot be transferred to this
joint map. The [machine report](results/joint-mask04-tx-prom-edge.json)
contains the trace, raw-byte and mapped-code hashes, phase metrics and
source hashes.

The same saved edge capture now screens four explicit A2 output behaviors
through the fixed 1,950 Hz, Q=1 bandpass. This is an **assumed line stage**;
the photo has not established its transfer function or a mode gate.

| A2 DAC behavior | Late-A2 RMS / late-A1 RMS, both modes, phases and six buses | A3/A4 errors per case |
| --- | ---: | ---: |
| Pass through the changing executed codes | 0.998245–0.998451 | 0/62 |
| Hold the last A1 code | 0.000000 (six decimals) | 0/62 |
| Force code 128 | 0.000000 (six decimals) | 0/62 |
| Force code 0 | 0.000000 (six decimals) | 0/62 |

Thus this bandpass model needs the A2 code to stop changing to reproduce
silence; it does **not** single out a mid-code gate. A held 74LS273/74LS373
output, a DAC-code override, or a later analog mute remain separate wiring
hypotheses. All four controls preserve the later data decisions because the
filter has settled by A3/A4. The report records every bus, phase and selector
case, including the different held codes.

This is a useful C2/C3 **mapping-compatibility** result: the same fixed
field map that retains the tested ADC response can produce the candidate
2,100 Hz tone and dibit-following DAC codes under a raw-PROM edge.
It does not identify the physical line output. The 375:1 divider,
U10-to-latch clock, Y-to-74LS273 data wiring, six possible DAC bus orders,
A2 hold/mute behavior, analog bandpass and connector route remain assumptions.
C2 stays open; neither an identical filtered score nor a differing hash
selects the true latch phase. The next discriminating test should constrain
one of those connections or the analog response using existing photos and
new independent control/data stimuli, without waiting for continuity.

Reproduce from the microcode directory with
`python3 g2/joint_mask04_tx_prom_edge.py`.
