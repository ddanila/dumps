# Offset-tolerant PROM readout into the paced controller zero detector

The [ADC-margin readout](RECEIVER-MASK04-ADC-MARGIN-SELECTOR.md) recovered
random data on fresh ±7 Hz streams, but had not carried the controller's
actual scrambled zero-run through the USART handoff. This
[replay](receiver_mask04_margin_zero_handoff.py) uses the unchanged 8031
scrambler-derived line octets for eight zero bytes under delays 5 and 18.
Each line stream becomes 32 DPSK data dibits after a 32-symbol `11`
reversal preamble. Four real-PROM runs cover ±7 Hz at 75° for delay 5 and
at 165° for delay 18. Each executes 768,047 words and accepts 24,000
complementary ADC visits. The three capture pairs, two decision tables
and ADC-margin ranking are frozen from the prior experiment.

| Scrambler delay, phase | Carrier offsets | PROM decisions | Recovered line bytes | Paced aligned controller |
| --- | --- | --- | --- | --- |
| 5, 75° | −7, +7 Hz | 0 wrong, 0 unknown / 63 measurable in each run | `62 DE 61 9D 7C 5F E5 E2` | Eight decoded zero bytes; `AF→B0` |
| 18, 165° | −7, +7 Hz | 0 wrong, 0 unknown / 63 measurable in each run | `A5 C2 4C 58 52 47 65 B4` | Eight decoded zero bytes; `AF→B0` |

The first differential dibit cannot be observed and remains a boundary
assumption. All other 31 preamble dibits and all 32 data dibits are
recovered from executed PROM output in every run. The recovered data
serializes LSB first to the eight line bytes above; none is filled from
the reference answer. The narrow 8251A external-sync model clocks those
bytes at an assumed 416 8031 machine ticks per bit while the unchanged
8031 ROM runs its main loop. An assumed SYNDET pulse before bit 64 lets
the controller consume all eight bytes without overrun and reach `AF→B0`.
Pulses at 63 or 65, no pulse, and the opposite DTE selector leave it at
`AF` in every case.

The [DSU 3556 front photo](../../../photos/PXL_20261123_114723348.jpg)
shows the two 8251A packages; the [DED 3558 front photo](../../../photos/PXL_20261123_114854803.jpg)
shows the ADC candidate and surrounding digital logic. Their back photos
([DSU](../../../photos/PXL_20261123_114730247.jpg),
[DED](../../../photos/PXL_20261123_114901193.jpg)) do not expose a continuous
inter-board RxD/RxC/SYNDET route. The 14.4 MHz DSC and 11.9808 MHz 8031
oscillators make 6,000 DSC cycles per 2,400 bit/s bit and 416 modeled
8031 ticks per bit plausible, but the actual divider, symbol capture
clocks, ADC bus, selector logic, serializer and sync pulse source remain
unverified. The processors are run sequentially; the 8251A model is
narrow, Timer 1 is disabled, and 8031 mode-0 input and serial completion
are synthetic. This is a **conditional behavioral handoff**, not C3.

Next constrain the candidate latch/selector and inter-board serial route
from visible pins or independent timing behavior, then run the same
frozen readout with naturally timed controller events and additional
offset/data fixtures. Missing continuity does not block those tests.

The [machine report](results/receiver-mask04-margin-zero-handoff.json)
records each PROM trace and ADC hash, selected capture counts, recovered
bytes, controller controls and source hashes. Reproduce from the
microcode directory with
`python3 g2/receiver_mask04_margin_zero_handoff.py`.
