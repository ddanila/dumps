# Paced external-sync bytes reach the uninterrupted 8031 receive loop

The earlier [external-SYNDET handoff](RECEIVER-MASK04-EXTERNAL-SYNC-HANDOFF.md)
offered each assembled byte to a separately entered `AF` routine when it
asked for one. This [timed replay](receiver_timed_controller_handoff.py)
instead runs the unchanged 8031 ROM continuously from main-loop address
`1ED3`. A narrow 8251A model clocks the saved real-PROM receive stream into
RxD every **416 modeled 8031 machine ticks**, raises RxRDY after each octet,
and keeps it raised until the ROM actually polls port 05 and reads port 01.
The 416-tick period follows the explicit classic-8031 clock hypothesis:
11.9808 MHz ÷ 12 ÷ 2,400 bit/s. The stream has 64 reversal-preamble ones
followed by eight PROM-derived line bytes; its first preamble dibit is supplied
by the reference fixture because the differential readout cannot observe it.

The continuously executed controller selects the receive descrambler
polynomial from its synthetic DTE frame. Selector `40` chooses delay 5 and
selector `60` chooses delay 18. The probe uses the matching selector for each
stream and tests the opposite selector as a control. It also keeps the earlier
SYNDET pulse placements, where bit 64 is the first data bit.
This is the **opposite direction** from the controller's transmit scrambler:
the call selector sends delay-18/GPC and receives delay-5/GPA, while the
answer selector sends delay-5/GPA and receives delay-18/GPC.

| Pulse before RxC bit | Characters consumed | Controller result in all four delay/angle fixtures |
| --- | ---: | --- |
| 56, one byte early | 9 | `AF`; zero count 5 |
| 63, one bit early | 8 | `AF`; zero count 5 |
| **64, first data bit** | **8** | **`AF→B0`; eight decoded zero octets** |
| 65, one bit late | 7 | `AF`; zero count 4 |
| No pulse | 0 | `AF`; zero count 0 |

For each aligned case, the 8031 makes 69 modeled status reads, consumes all
eight bytes, and has **zero receive overruns**. Byte-read latency ranges
from 59 to 672 machine ticks across the four fixtures, below the 3,328-tick
character interval. `B0` is reached at tick 53,366 for delay 5 and 53,340
for delay 18. With the opposite selector, the same eight line bytes are
consumed without overrun but decode to nonzero values and leave state `AF`.
This shows that naturally paced reads and the controller's own selector do
not break the conditional receive handoff.

The final completed mode-0 frame is `D0 47 A1 1A` in this continuous-loop
fixture. It differs from the earlier direct-call probe's `D0 42 81 1A`
because other controller routines also run between receive polls; the `B0`
state and zero count, not those frame bytes, are the shared signature.

This is still conditional. RxD, RxC, SYNDET and the two-bit serializer are
untraced; the SYNDET pulse is supplied at a chosen bit boundary. The 8251A
model covers only external sync, shifting and RxRDY. Timer 1 is disabled,
RAM15 is held positive at state dispatch, DTE frames are synthetic, and SBUF
completion is forced after eight emulator ticks. PROM-derived bits are read
from saved traces rather than generated concurrently with the 8031. C3 and
G2 remain open. The [machine report](results/receiver-timed-controller-handoff.json)
contains all byte completion/read times, decoded bytes, controls and source
hashes. Reproduce from the microcode directory with
`python3 g2/receiver_timed_controller_handoff.py`.
