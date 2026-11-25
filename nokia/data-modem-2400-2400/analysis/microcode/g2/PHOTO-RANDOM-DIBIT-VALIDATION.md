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
six survivors share the same routes for source bits **0, 2, 4, 6 and 7**:
they map to candidate DAC code bits **4, 5, 3, 6 and 7**, respectively.
Under the ordered-Y-to-latch hypothesis, those are DAC inputs B4, B3, B5,
B2 and B1. Source bits **1, 3 and 5** can map to code bits **0, 1 and 2**
(DAC B8, B7 and B6) in any order. The earlier prose incorrectly described
the fixed bits as 3–7; the saved permutations were correct. These decisions
still cannot recover the complete physical bus. The [saved report](results/photo-random-dibit-validation.json)
records all 12 per-stream scores, survivors, full-PROM trace digests,
sample hashes and source hashes.

This strengthens the **conditional** transmitter interpretation: the phase
rule carries arbitrary nonperiodic dibits, beyond the tested controller
pattern, through a ROM-checked sample path that an independent receiver can
decode. It does not prove the parity/counter decoder, D127 input wire, DAC
latch clock, seven untraced DAC bits, analog line output or DSC receive/echo
processing. Keep C2 open until the output route and waveform are independently
constrained.
