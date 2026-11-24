# What the 3C5 and 3DA tables do under photo-constrained fields

The G1 [Q-independent mapping](../assumed/Q-INDEPENDENT.md) makes the
four-entry tables at 3C5 and 3DA perform quarter-turns of a 16-bit pair:
`(X,Y), (−Y,X), (−X,−Y), (Y,−X)`. Those identities were constraints in the
mapping search, so they are not independent proof of the board's algorithm.
The later [photo candidates](PHOTO-FIELDS.md) instead place part of the B
register address in U11's latch, A2/A3 in U10's latch, and may tie U2 A0
and I7 to the same U6 Q0 signal. This changes the table operands and writes.

[`photo_transform_check.py`](photo_transform_check.py) executes each table
entry's four real-PROM words in the Am2901 model for three nonzero/boundary
source pairs. The original G1 q3 mapping still passes **24/24** quarter-turn
checks. For each of the five current photo-constrained mappings, the probe
tests both I0 levels and **all 16 possible four-word levels of the candidate
A0=I7 signal**. It retains the G1 carry policy and even allows PROM data to
be held during an E4-low word. No one of those 32 pin-level combinations
passes any of the 24 quarter-turn checks. The [saved report](results/photo-transform-check.json)
records every pattern and a q3 witness.

The reason is visible in the decoded controls. In all 32 words of these two
tables, a low I7 selects destination code 1, **no RAM write**; a high I7
selects destination code 3, **RAM[B] write**. If A0 is the same signal, a
word that reads an even A register cannot write its result. Holding the
signal high permits writes but makes the two bytes of each source pair read
the same odd A register. For example, with source words `X=1234` and
`Y=5678` (hex), all-high q3 produces `1212,5656` at entry 0 instead of
`1234,5678`. This is a structural conflict between the simple coupled-pin
hypothesis and a 16-bit quarter-turn at these tables; it is not a proof that
the board never uses another timing or field mapping.

An uncoupled diagnostic isolates the photo A/B reassignment. It fixes I7=1,
I0=0, and alternates A0 as `0,1,0,1` across each four-word entry. All five
mappings then pass **24/24** checks for the *different* transform
`(X,Y), (X,−Y), (−X,−Y), (−X,Y)`; only 12/24 quarter-turn checks survive.
For `X=1234, Y=5678`, q3's entry 1 gives `1234,A988`, whereas a
quarter-turn would give `A988,1234`. This sign selection could be useful in
quadrature processing, but the controller's table index, source pairs,
physical pin timing and output destination have not been identified.

The table fixtures are local four-word datapath runs. They do not demonstrate
a controller-driven modulator, a DAC sample stream, a receiver or echo
canceller. The photo segments retain pad/via uncertainty; the uncoupled
control deliberately violates the candidate A0/I7 tie. These runs retain a
shared instruction across both Am2901 slices; the [separate-slice candidate](SPLIT-SLICE-PROBE.md)
could alter the table behavior.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/photo_transform_check.py
```
