# External-byte poll at 1EC

The original-register, previous-flag zero-input reset example in
[the condition study](DEFINED-CONDITIONS.md) stalls at 1EC. A changing external
input releases that loop without changing its conditions, dispatch, starting
registers, or microcode. This supports a provisional external-byte equality
poll interpretation under that decode.

At 1EC, the ALU computes `(D + R4) mod 256`, stores it in R3, and outputs the
unchanged R4 on Y. At 1ED, the previous-zero condition repeats the loop while
that sum is nonzero. Therefore the release byte is `(-R4) mod 256`. The return
at 1EE ends the routine. The ALU operation at 1ED is R0 AND Q; using its current
zero flag instead would test a different quantity, independent of this D read.
This study preserves the previous-flag policy; it does not establish the
physical condition timing.

## Reset experiment

All six runs start from 000, run 1,000 cycles, and first reach 1EC at cycle 188
with R4=FF. Cycle numbers are zero based.

| External values sampled at successive visits to 1EC | Poll visits | First 1EE | Final PC |
| --- | ---: | ---: | --- |
| 00 held | 406 | none | 1EC |
| 02 held | 406 | none | 1EC |
| 01 held | 1 | 190 | 084 |
| 00, then 01 held | 2 | 192 | 084 |
| Three 00 reads, then 01 held | 4 | 196 | 084 |
| Seven 00 reads, then 01 held | 8 | 204 | 084 |

All runs complete without stack violations. Each unsuccessful poll costs two
microinstructions. Successful release reaches the existing terminal self-loop
at 084; this is not evidence of continuous modem operation or a recovered
restart mechanism. The held-input cases are finite observations, with the
local arithmetic explaining why those inputs cannot satisfy the comparison.

## Explicit input assumption

[polling-study.json](polling-study.json) specifies the sequences. The runner's
`pc_sequence` read mode uses independent visit counters for canonical decimal
instruction addresses. Each visit to a listed PC consumes one entry; after
the sequence ends its last byte is held. Unlisted PCs receive the default byte.
Visits count even when the ALU does not select D, and each read records whether
D was selected, the visit and sequence index, and whether the last value was
held. These are instruction-address-keyed stubs, not recovered peripheral
addresses, hardware clocks, or controller responses. Existing preparation
inputs are retained as one-element sequences.

The physical source of D and the purpose of this comparison remain unknown.
No DAC, sampling event, or 8031 handshake is inferred from the poll alone.

## Reproduction and checks

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/polling_study.py
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -p 'test_*.py'
```

[Report](results/polling-study/report.json) includes every poll observation and
return cycle. Each run saves its mapping, scenario, full bounded trace, I/O log,
and summary. The study checks every observed sum and following branch, as well
as the predicted first-return delay. Unit tests cover all 65,536 D/R4 pairs for
the decoded operation, independent per-PC sequence consumption, hold-last and
default behavior, and malformed sequence/provenance rejection.
