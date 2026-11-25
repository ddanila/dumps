# Nonperiodic dibits narrow the candidate DAC bus family

The [exhaustive DAC screen](PHOTO-DAC-BUS-PERMUTATIONS.md) found 12
photo-B5-compatible byte orders with zero errors on 104 controller-stream
decisions. That short set could leave a bus-order fit that only works for
those particular streams. The [seeded holdout](photo_random_dibit_validation.py)
feeds four new 256-symbol, nonperiodic dibit sequences through the same
labelled four-visit D127 pulse rule and tests all 12 orders with the fixed
four-sample receiver alignment. It does not refit the rule, receiver or bus
orders. These are synthetic input streams, separate from the executed 8031
bytes.

For the first 32 symbols of each of two seeds, a full real-PROM run verifies
every `129` ROM address, ROM byte and Am2901 Y value. Each run captures 256
candidate samples; its byte-stream hash matches the recurrence used to
project the longer streams. All 48 bus/stream decision scores also agree
with a direct invocation of the independent reference receiver.

| Bus family from the prior 12 | Total wrong decisions / 1,016 | Count |
| --- | ---: | ---: |
| Surviving orders | 0 | 6 |
| Rejected orders | 5, 9 or 10 | 6 |

The four streams each yield 254 decisions after the fixed four-sample
alignment. A no-pulse carrier control makes 186–198 errors per stream. The
six survivors share the same routes for source bits 3–7: bits 3, 4, 5, 6,
7 map to candidate DAC code bits 5, 3, 4, 6, 7 respectively. Their source
bits 0–2 can map to output bits 0–2 in any order, so these decisions still
cannot recover the complete physical bus. The [saved report](results/photo-random-dibit-validation.json)
records all 12 per-stream scores, survivors, full-PROM trace digests,
sample hashes and source hashes.

This strengthens the **conditional** transmitter interpretation: the phase
rule carries arbitrary nonperiodic dibits, beyond the tested controller
pattern, through a ROM-checked sample path that an independent receiver can
decode. It does not prove the parity/counter decoder, D127 input wire, DAC
latch clock, seven untraced DAC bits, analog line output or DSC receive/echo
processing. Keep C2 open until the output route and waveform are independently
constrained.
