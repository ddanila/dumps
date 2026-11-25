# A candidate external SYNDET pulse clocks PROM-derived data into the 8251A receive path

The controller's executed programming sequence is `CC FF 15` for line-side
USART 01/05. In the [Intel 8251A datasheet](https://deramp.com/downloads/intel/8251A.pdf),
`CC` selects synchronous eight-bit characters with **external** sync
detect. The `FF` character can be sent as transmit fill, but it does not
make the receiver hunt internally. A positive-going signal on SYNDET pin
16 makes the receiver start assembling characters at the next RxC rising
edge. RxD is pin 3 and RxC is pin 25. The earlier
[`FF` hunt screen](RECEIVER-MASK04-SYNC-HUNT-ALIGNMENT.md) is therefore a
counterfactual framing test for this controller mode.

The [external-sync replay](receiver_mask04_external_sync_handoff.py)
consumes the saved real-PROM receive bytes and trace digests from the
[controller zero-run handoff](RECEIVER-MASK04-CONTROLLER-ZERO-HANDOFF.md).
It reconstructs the 64-bit `11` reversal preamble, with its first dibit
explicitly supplied because a differential decision cannot observe it,
then clocks 64 PROM-recovered data bits at an assumed 6,000
microcycles/bit. A narrow 8251A model samples RxD at each RxC rising edge,
uses an assumed one-bit SYNDET pulse to start LSB-first assembly, raises
RxRDY after each octet, and supplies those octets to the preserved 8031
ROM's state-`AF` status/data-read probe. The model assumes the CPU reads
each completed character immediately; it is not a full chip or naturally
timed CPU/USART co-simulation.

| SYNDET pulse before RxC sample | USART output | 8031 result, both scrambler delays and both 0°/45° receive traces |
| --- | --- | --- |
| One byte before data, at bit 56 | `FF` then eight correct line bytes | `AF`, zero counter 5; `D0 42 89 9A` |
| One bit before data, at bit 63 | Eight misaligned bytes | `AF`, zero counter 5; `D0 42 89 9A` |
| **First data bit, at bit 64** | **Eight exact PROM-derived line bytes** | **`AF→B0`, eight zero octets; `D0 42 81 1A`** |
| One bit after data begins, at bit 65 | Seven incomplete-stream bytes | `AF`, zero counter 4; `D0 42 89 9A` |
| No pulse | No RxRDY or data bytes | No controller read attempted |

The byte-early pulse is informative: even though all eight correct line
bytes eventually arrive, the preceding `FF` alters the controller's
preserved descrambler history, so the executed zero detector does not
reach `B0`. The bit-shift controls likewise fail. The
[machine report](results/receiver-mask04-external-sync-handoff.json)
records every assembled byte, RxRDY event, controller output and source
hash. This narrows the pulse's **required timing under this fixture**; it
does not establish that the modem supplies such a pulse at the A3/data
boundary.

SYNDET's source, RxD/RxC wiring, the 6,000-cycle clock and the two-bit
serialization remain photo-compatible **assumptions**. The phase readout
used by the earlier 0°/45° real-PROM traces is also external, and this
replay consumes saved traces rather than executing new PROM cycles. C3
remains open. Next test a visible or pin-compatible candidate for SYNDET
and the bit serializer against executed controller mode timing and fresh
receive streams. Reproduce from the microcode directory with
`python3 g2/receiver_mask04_external_sync_handoff.py`.
