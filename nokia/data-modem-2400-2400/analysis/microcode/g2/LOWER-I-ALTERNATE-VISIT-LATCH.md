# Alternating-visit direct DAC latch does not make a held-input carrier

The [reproducible run](lower_i_alternate_visit_latch.py) continues the
[eight-visit `08/09` controller stream](LOWER-I-FOUR-SAMPLE-BIT-SCREEN.md).
It hypothesizes a 153.6 kHz microcycle: the eight-word loop makes 19,200
visits/s and an adjacent 74LS273 clocks every second visit at 9,600 Hz.
Both alternating-visit phases were tested. Candidate latch inputs were ALU
Y at `3F8`, `3F9`, or `3FA`, R10 after `3F7`, and the selected `3F7`
Am27S31 byte with and without B8 inversion. The locally executed
128-bit controller stream and both constant-input controls each made all
1,024 requested loop visits. The [JSON report](results/lower-i-alternate-visit-latch.json)
contains the captured bytes, 64-sample spectra, trace digests and twelve
candidate source/phase cases.

For held `08`, every second-visit sampled source is constant in the tested
window after the first 128 visits.
Consequently no full-byte route or bit permutation of these six direct
sources can produce a steady 1,800 Hz carrier for that input and this clock.
Held `09` yields short six-sample patterns or other non-carrier peaks; neither
phase has a 1,800 Hz full-byte peak for both held levels. None of the eight
possible source bits offered to the photo-candidate DAC08 B5 route has a
1,800 Hz peak under either held level. Two 64-sample controller-stream
windows peak at 1,800 Hz: `3FA` phase 1 carries 12.6% of its spectral power
in that bin, and the raw/inverted `3F7` ROM-byte pair at phase 0 carries
10.4%. Their held controls fail, so neither identifies a transmitted carrier.

This excludes **these direct source/clock fixtures**, not the active G2
goal. The 8031-to-D3F8 route, PROM/latch control, byte bus and clock are
untraced, and a held D3F8 bit is not proven to represent a steady dibit.
The next experiment should look for a staged DAC byte update, another
clock phase or a command-dependent signal path while retaining the real
PROM and controller stream. New continuity measurements could discriminate
those candidates but are not needed to run them.
