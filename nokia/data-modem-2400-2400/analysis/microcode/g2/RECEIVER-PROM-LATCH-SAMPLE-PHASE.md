# The PROM-decoded `3FA` latch byte is not a usable PCM sample in this fixture

The [raw-PROM row gate](RECEIVER-PROM-ROW-LATCH-GATE.md) gives a concrete
three-input-NAND clock hypothesis: it captures the prior `3FA` Y byte as
`3ED` begins, once per four-row ADC-table visit. Five full traces showed
that byte changes with the input. This screen tests the next necessary
claim: whether a sample-rate divider and fixed differential receiver can
decode independent line data from those captured bytes.

Eleven independent 192,047-instruction real-PROM streams use the same joint
upper-source mask-08 mapping, assumed four-row dispatch, inverted
previous-overflow TEST, and complementary ADC input. Seven streams form
the three-training/four-holdout screen; four fresh random streams validate
the selected readout. Every stream selects 6,000 ADC bytes at `3F8` and
reaches 6,000 `3FA` bytes. The modeled ADC holds each reference sample for
47 or 46 table visits. The screen tests all 47 possible visit phases,
offset-binary and two's-complement coding, and five symbol lags. A fixed
*external* reference receiver performs the differential decisions.

| Result | Dibit errors |
| --- | ---: |
| Exact training fits among 470 readouts | 0 |
| Best training choice, phase 7, offset binary, lag +2 | 23/36 |
| Same choice on holdout | 38/48 |
| Same choice on four fresh streams | 9/12, 9/12, 9/12, 10/12; 37/48 |
| Reference PCM on four fresh streams | 0/48 |

The decoded byte stream does not behave as a usable PCM sample under this
fixed decoder, despite its input-dependent values and exact PROM edge
cadence. This excludes the tested **Y-only, sample-rate-divided readout**;
it does not exclude another latch data source, multi-byte processing,
mode-dependent timing or a separate serial decision circuit. The decoder
is external diagnostic code and no USART-01 RxD path is identified. C3
remains open. Search the photographed output path for a different data
source or an executed stateful decision instead of promoting this clock
candidate into a receiver claim.

The [machine report](results/receiver-prom-latch-sample-phase.json) records
the chosen phase, train/holdout/fresh scores, full-state trace digests and
source hashes. Reproduce with
`python3 g2/receiver_prom_latch_sample_phase.py` from the microcode
directory.
