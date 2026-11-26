# Frozen row-byte phase logic on the full-byte line candidate

The [gap audit](JOINT-MASK04-FULL-BUS-OFFSET-GAP-AUDIT.md) showed that the
earlier [phase-47 Boolean readout](RECEIVER-MASK04-PHASE47-BOOLEAN-DIBITS.md)
gets two selected offset gaps right. This test applies that **unchanged**
row-0/row-3 gate, previous-symbol phase subtraction and dibit map to
complete full-byte real-PROM receive traces. It keeps the two previously
frozen non-zero line-byte streams, DAC order, `127` sample site, analog
filter, ±7 Hz shift and preamble AGC. Phase 47 is the original frozen
capture site; 46, 48, 93 and 94 are exploratory adjacent sites, not a
fitted selector.

The six ADC hashes and 780,047-instruction receive trace digests match
the prior full-byte offset challenge. The independent reference receiver
still decodes all 64 differential decisions in every case without error.
The old row logic, however, does not transfer to this waveform:

| Selector | Offset | Data dibit errors at frozen visit 47 | Best error count among five inspected visits | Exact eight bytes? |
| --- | ---: | ---: | ---: | --- |
| `40` call | −7 Hz | 15/32 | 15/32 | No |
| `40` call | 0 Hz | 18/32 | 15/32 | No |
| `40` call | +7 Hz | 17/32 | 15/32 | No |
| `60` answer | −7 Hz | 10/32 | 10/32 | No |
| `60` answer | 0 Hz | 20/32 | 15/32 | No |
| `60` answer | +7 Hz | 16/32 | 15/32 | No |

At its frozen visit the rule misses 96 of 192 data dibits across the six
cases. Even zero-offset controls fail, so the prior two correct gap
snapshots do not support using this gate as a full-stream repair. Its
earlier 0/96 fresh result remains valid for the **different reference
waveform and carrier-phase fixture** on which it was tested. The gate is
an external hypothesis, not executed DSC logic; this negative transfer
does not establish the Nokia receiver's actual decision route.

Next, retain complete executed row-byte sequences from the full-byte
fixtures and derive a causal readout there, separating development and
fresh payload/phase validation. Alternatively test a different labelled
ADC, latch or clock route. Keep C3 open and G2 active.

Run `python3 g2/joint_mask04_full_bus_row_logic_offset.py` from the
microcode directory. The [machine report](results/joint-mask04-full-bus-row-logic-offset.json)
records all five phase scores, recovered bytes, ADC/PROM hashes and source
hashes.
