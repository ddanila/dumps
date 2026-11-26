# Two-visit PROM decisions reach the paced controller zero detector

The [dual-feature receive readout](RECEIVER-MASK04-DUAL-FEATURE-CONSENSUS.md)
recovers every measurable dibit in the held-out 13-angle data stream, but
that stream was too short to exercise the controller's eight-octet zero
detector. This [handoff run](receiver_mask04_dual_zero_handoff.py) uses 32
`11` reversal symbols followed by the **actual eight scrambled line octets**
for eight zero bytes under the controller's two scrambler delays. It tests
75° with delay 5 and 165° with delay 18. The fixed joint mask-`04` mapping
executes 768,047 real-PROM words per case, accepting 24,000 complementary
ADC visits. The script captures only executed `3F8` Y at symbol-relative
ADC visits 47 and 94, then applies the two frozen readouts and their
conservative consensus. The input PCM and conversion schedule remain
explicit board hypotheses.

| Case | PROM consensus | Recovered line bytes | Paced aligned controller |
| --- | --- | --- | --- |
| Delay 5, 75° | 0 wrong, 0 unknown / 63 measurable dibits | `62 DE 61 9D 7C 5F E5 E2` | 8 bytes consumed, 8 decoded zeros, `AF→B0` |
| Delay 18, 165° | 0 wrong, 0 unknown / 63 measurable dibits | `A5 C2 4C 58 52 47 65 B4` | 8 bytes consumed, 8 decoded zeros, `AF→B0` |

The first reversal dibit is not measurable by a differential receiver;
its two `1` bits are supplied to the narrow 8251A model as an explicit
boundary assumption. The other 31 preamble dibits are recovered from the
PROM run and are all `11`. The 32 data dibits serialize LSB first into
the eight bytes above; they equal the controller-derived line bytes
without substituting expected bits for an unknown decision. At 165° the
primary readout alone has one unknown data dibit, while the alternative
supplies it. The two readouts have no conflicting known labels in either
run.

The existing [paced external-sync model](RECEIVER-TIMED-CONTROLLER-HANDOFF.md)
clocks those recovered bytes at an assumed 416 8031 machine ticks per bit
while the unchanged 8031 ROM executes its main loop. A SYNDET pulse just
before RxC bit 64 delivers all eight bytes without overrun, descrambles
eight zeros and moves state `AF→B0` in both cases. A pulse at bit 63 or
65, no pulse, and the opposite DTE selector stay at `AF`; the no-pulse
control produces no receive-ready bytes. The machine report retains the
per-byte completion/consumption cycles and every control result.

This closes a **conditional behavioral handoff**, not C3. The ADC gate,
two symbol-relative capture clocks, five-bit readout logic, previous
symbol memory, bit serializer, RxD/RxC/SYNDET nets and SYNDET pulse
source are not established from the photographs. The 8251A model covers
only external-sync shifting and RxRDY behavior; the 8031's mode-0 input
and serial completion are synthetic, Timer 1 is disabled, and the two
processors execute sequentially. No line-board receive signal or physical
USART event has been measured. Next test a photo-compatible latch/clock
route for the five captured bits, then tighten the serial timing and
SYNDET source. Missing continuity does not pause those experiments.

The [machine report](results/receiver-mask04-dual-zero-handoff.json)
records trace/source hashes and all control outcomes. Reproduce from
the microcode directory with `python3 g2/receiver_mask04_dual_zero_handoff.py`.
