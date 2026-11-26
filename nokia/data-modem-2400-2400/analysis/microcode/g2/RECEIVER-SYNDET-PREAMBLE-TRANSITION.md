# First non-reversal data is not a general SYNDET source

The long [frame-mode receive handoff](RECEIVER-MASK04-FRAME-MODE-ZERO-HANDOFF.md)
places an external SYNDET pulse just before the first data RxC edge.
One tempting circuit would watch the repeated `11` reversal preamble
and pulse when the first decoded dibit is not `11`. This
[screen](receiver_syndet_preamble_transition.py) checks that proposal
against the ROM-validated controller scrambler model and the paced
8251/8031 model.

For each receive descrambler delay, the script varies all 256 possible
first payload octets, holds the following seven payload octets at zero,
and generates the corresponding line bytes from the controller scrambler
state. The first non-`11` data dibit occurs at these offsets from the
true data boundary for **both** delays:

| Dibit offset | Number of 256 first payload octets |
| ---: | ---: |
| 0 | 192 |
| 1 | 48 |
| 2 | 12 |
| 3 | 3 |
| 4 | 1 |

Thus the proposed pulse is late for 64/256 first octets. This is a
data-dependent failure, not an analog timing margin. The existing
eight-zero-octet fixture happens to fall in the offset-0 group for
both directions, so its successful aligned handoff cannot validate
this detector.

The script compiles the existing paced 8251/8031 probe and exercises a
representative offset-1 payload for each delay. With SYNDET at bit 64,
the controller consumes the offered first line bytes `43` (delay 5)
and `A7` (delay 18). Pulsing at the detector's first non-`11` dibit,
bit 66, makes the consumed first bytes `90` and `A9`, respectively;
the serial character boundary has shifted. The following bytes also
change. The detector circuit is hypothetical, and this test uses
controller-derived bytes rather than a new DSC PROM run, but it shows
why the current zero-run handoff cannot derive SYNDET from the first
data change alone.

The [controller frame timing](CONTROLLER-SYNDET-EDGE-TIMING.md) gives a
different candidate event before the *local transmitted* data byte;
it does not locate the first arriving remote bit. C3 therefore still
needs an independently timed sync source, such as a photo-compatible
frame/clock route tied to receive timing, or a receiver event that
marks the segment boundary regardless of payload. Keep the existing
aligned-pulse run conditional.

The [machine report](results/receiver-syndet-preamble-transition.json)
records every offset count, representative line bytes, paced controller
results and source hashes. Reproduce from the microcode directory with
`python3 g2/receiver_syndet_preamble_transition.py`.
