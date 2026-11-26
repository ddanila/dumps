# A candidate `3FA` capture keeps one distinction lost by the U12 row pair

The [U12 collision test](JOINT-MASK04-U12-CODE-COLLISION.md) offered two
matched ADC streams, differing only at sample 25: `1F` versus `6F`. Their
proposed row-0/row-3 U12 readout was identical. This
[mask-04 replay](joint_mask04_3fa_gate_collision.py) instead clocks a
candidate latch from either of the two previously found three-input
raw-PROM decodes for `3FA`. Both decodes remain high only at `3FA` and
produce exactly 3,000 `3FA→3ED` NAND rising edges in each of three
96,047-instruction real-PROM runs. They capture the same Y byte on every
edge.

For the matched pulse pair, the captured byte differs on precisely the
47 visits that hold the changed sample, visits 1172–1218. It is `20`
for `1F` and `21` for `6F` on every affected visit. This is a one-bit
distinction preserved by the executed `3FA` output and a candidate clock,
where the tested U12 row pair lost it. It is still an artificial pulse,
not a pair of legal dibits.

A separate eight-symbol, 75° rotated carrier uses dibits
`1 1 2 3 0 0 3 2`, which the independent reference receiver decodes
exactly. The candidate latch captures 3,000 bytes; they take only the
values `20` and `21`, with bit 0 high on 375 visits. At symbol-relative
visit 47 the values are `21 20 21 20 20 21 20 20`; at visit 94 they are
`20 20 20 20 21 20 20 20`. The output changes on a valid waveform,
but these fixed visits do not themselves supply a four-way dibit
decision. A temporal or multi-signal readout would still be needed.

The PROM decode, NAND-to-latch clock, Y-bus data pins and consumer are
photo-compatible assumptions, not identified board nets. This result
does not establish RxD or close C3. Next test whether a timed history of
this one-bit capture, together with another executed output, can resolve
independent legal dibits and reach the serial handoff. A failed readout
would reject that stated route without blocking G2.

The [machine report](results/joint-mask04-3fa-gate-collision.json)
contains trace/input/capture hashes and the two gate definitions. Reproduce
from the microcode directory with
`python3 g2/joint_mask04_3fa_gate_collision.py`.
