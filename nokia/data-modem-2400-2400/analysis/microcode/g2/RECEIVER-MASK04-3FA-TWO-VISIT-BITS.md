# Two fixed visits of `3FA` Y0 do not decode independent dibits

The [candidate `3FA` latch](JOINT-MASK04-3FA-GATE-COLLISION.md) preserves
an ADC distinction lost by the tested U12 row pair and emits only `20`
or `21` on one legal carrier. This [new screen](receiver_mask04_3fa_two_visit_bits.py)
asks whether the low bit at **two fixed visits per symbol**, together
with the preceding symbol's same two bits, determines a dibit. That
four-bit transition key has at most 16 values. The lookup and symbol
clock are external diagnostics; this tests information in a particular
capture route, not a DSC-executed decision circuit.

Six full real-PROM receiver runs use three independent 16-dibit data
seeds at 45° and 135° carrier rotation. Each executes 192,047 words
and reaches 6,000 selected ADC visits and `3FA` outputs. The four runs
shared with the earlier carrier-phase screen reproduce its exact trace
and ADC hashes. In all six, `3FA` Y is only `20` or `21`; bit 0 changes
with the input. The offered PCM is independently decoded without error.

The first seed at both rotations trains a fixed lookup over all
**70,125** distinct pairs of symbol-relative visits. The next two
seeds are held out. A conflicting training key is reported as unknown
rather than assigned a convenient label.

| Selected visits | Training | Holdout | Fresh |
| --- | ---: | ---: | ---: |
| 140 and 235 | 0 wrong, 13 unknown / 24 | 1 wrong, 22 unknown / 24 | 3 wrong, 15 unknown / 24 |

No visit pair gives a conflict-free, fully known training table; the
maximum known training decisions are **11/24**. The selected table is
frozen using training results only. Its poor holdout behavior shows
that this particular two-visit, one-bit candidate does not justify a
USART RxD stream. It does not reject longer histories, other `3F8`/
`3F9` outputs, adaptive timing or a separately clocked external
decision circuit. The gate-to-latch and onward serial nets are still
photo-compatible assumptions; C3 remains open. Next test a multi-signal
consumer constrained by the photos or a phase-aware temporal readout
on fresh data, and continue without waiting for missing continuity.

The [machine report](results/receiver-mask04-3fa-two-visit-bits.json)
contains each trace/input/output hash, the selected lookup and all
scores. Reproduce from the microcode directory with
`python3 g2/receiver_mask04_3fa_two_visit_bits.py`.
