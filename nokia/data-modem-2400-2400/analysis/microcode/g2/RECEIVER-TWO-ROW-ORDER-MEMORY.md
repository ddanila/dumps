# What the retained two-row state remembers

The [pulse-memory experiment](RECEIVER-TWO-ROW-PULSE-MEMORY.md) found Q, RAM and
PROM-address offsets that survive thousands of later baseline ADC visits. This
experiment distinguishes retained input *class* from retained sample *order*.
It runs the real PROMs for 3,000 ADC visits under the same hypothetical
complementary D3F8 input and alternating 0/2 dispatch fixture. Every run has
the same PC path. Two 94-visit ADC holds begin at visit 188; all later visits
offer `09`.

The `19,A9` and `A9,19` runs have identical byte counts but differ at every
one of the 2,624 visits after both holds. At visit 2,999, reversing the order
changes Q by 2, R10 and R11 by 1, and the next `3F9` PROM address by 1.
Relative to an all-`09` control, the final PROM-address offsets are 2 and 3,
respectively, and Q offsets are 6 and 8. Those final values match the
previously observed class of the **last** changed level in each order.

A matched-last-level control tests that explanation. `A9,19,A9` and
`19,A9,A9` contain the same three 94-visit holds in different order and both
end with `A9`. They first differ at visit 188, then fully reconverge by visit
378, inside the shared final `A9` hold. After the input returns to `09`, they
have **zero** Q/RAM/Y or PROM-address differences across all 2,530 later
visits. Under these levels and this fixture, the persistent late offset does
not encode the earlier order once the last changed class is matched.

This narrows the pulse-memory interpretation: the tested state behaves like
the latest retained input class, rather than evidence of a multi-sample phase
history or a decoded DPSK symbol. Other levels, timing, dispatch and wiring
remain open. The next receiver test should seek a state update that combines
successive samples under a photo-compatible route, or identify an actual
decision output in the executed program. The
[machine report](results/receiver-two-row-order-memory.json) records the
fixtures, source hash, trace digests and comparisons; reproduce with
`python3 g2/receiver_two_row_order_memory.py` from the microcode directory.
