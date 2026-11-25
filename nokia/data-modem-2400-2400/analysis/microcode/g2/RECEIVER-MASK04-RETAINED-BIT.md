# Mask-04 retained state has no direct received bit in this screen

The [joint-map screen](JOINT-FOUR-ROW-RETENTION-TX.md) found that mask `04`
retains ADC-dependent R1, R12 and Q through the complete four-row table,
while preserving the candidate transmitter waveform. This screen tests
whether a bit of those actual retained bytes is already a received dibit
bit. It uses the same real-PROM map, assumed counter-like dispatch,
inverted previous-overflow TEST and complementary ADC sample schedule.

Eleven independent 192,047-instruction streams each select 6,000 ADC bytes
and capture R1, R12 and Q after every `3FE`. Seven streams provide three
training and four holdout cases; four fresh random streams validate the
selected candidate. The screen checks all eight bits of each byte at all
375 table-visit phases per symbol, lags −2…+2, both output polarities,
and both a direct bit and its XOR with the previous symbol's bit.

No tested channel fits even the 36-dibit training set exactly. The best
direct result for target bit 1 is R1 bit 3 at phase 141, lag +1:
7/36 training and 5/48 holdout errors. The lowest training error across
the whole screen is 6/36 for previous-symbol XOR of R12 bit 4; that
candidate makes 10/48 holdout and 17/48 errors across four fresh streams.
These state bits contain some input information but none is a demonstrated
received bit. No output is tied to USART 01 RxD. C3 stays open; next test
an instruction-motivated multi-byte or stateful decision on this retained
map, or another photo-compatible output latch.

The [machine report](results/receiver-mask04-retained-bit-screen.json)
records the best per-operation candidates, all run digests, fresh scores
and source hashes. Reproduce with
`python3 g2/receiver_mask04_retained_bit_screen.py` from the microcode
directory.
