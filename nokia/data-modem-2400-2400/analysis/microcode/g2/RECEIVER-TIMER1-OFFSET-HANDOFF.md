# Timer 1 interrupts during the offset-PROM receive handoff

The [offset-PROM zero-run handoff](RECEIVER-MASK04-MARGIN-ZERO-HANDOFF.md)
reaches controller state `B0` with exact line bytes, but its paced 8031
probe disables Timer 1. This [replay](receiver_timer1_offset_handoff.py)
enables the same emulator Timer 1 configuration used by the earlier
[interrupt-paced controller run](MAIN-LOOP-TIMER1-SEGMENT2.md):
`TMOD=15`, `TH1=FC`, `TL1=21`, `TCON=40`, `IE=88`. It keeps the saved
real-PROM line bytes, 416 modeled 8031 ticks per RxC bit, initial `AF`
state, synthetic DTE input, held-positive RAM15 gate and narrow external
SYNDET/8251A model unchanged. A separately compiled timer-disabled probe
reproduces the saved handoff outputs exactly before comparison. One saved
−7 Hz PROM trace is selected for each delay; its recovered line bytes
also match the corresponding +7 Hz trace.

Both scrambler delays are tested with SYNDET at bit 63, 64 or 65 and
without a pulse, plus an opposite-selector control at bit 64. Each
timer-enabled controller run executes **57 Timer 1 ISR entries** with
no emulator errors or receive overruns.

| Delay | Pulse at bit 63 | Pulse at bit 64 | Pulse at bit 65 | No pulse | Opposite selector |
| --- | --- | --- | --- | --- | --- |
| 5 | `AF`, 5 zero octets | **`B0`, 8 zero octets** | `AF`, 4 zero octets | `AF`, 0 | `AF` |
| 18 | `AF`, 5 zero octets | **`B0`, 8 zero octets** | `AF`, 4 zero octets | `AF`, 0 | `AF` |

The aligned run consumes all eight PROM-derived line bytes for each
delay, descrambles eight zeros and finishes the controller's zero-run
transition. Its `B0` tick moves from 53,366 to 53,251 for delay 5 and
from 53,340 to 53,239 for delay 18 when Timer 1 is enabled. The longest
receive-byte completion-to-read latency among the tested timer runs is
778 ticks, below the 3,328-tick character interval. The controller
therefore tolerates modeled timer interrupts during this conditional
receive sequence.

The **unheld-RAM15 control** keeps Timer 1 active and uses the aligned
pulse, but no longer forces RAM15 positive at state dispatch. In both
delays it falls to state `00`, consumes no receive bytes, and records
seven USART overruns while eight characters complete. The positive
RAM15 gate is therefore necessary for this synthetic `AF` fixture;
the timer result does not establish that the real modem supplies it.

This still does not reconstruct the actual entry into `AF` or its
countdown: the probe starts from a preserved synthetic state. DTE input,
mode-0 serial completion, RxD/RxC/SYNDET route and pulse source remain
assumed; DSC and 8031 execute sequentially. C3 stays open. The next
useful timing test should derive both the RAM15 gate and `AF` entry from
the controller's preceding executed state, then test the sync event
without placing it directly, while retaining the same PROM receive data
and early/late controls.

The [machine report](results/receiver-timer1-offset-handoff.json)
includes all byte timings, ISR counts, frames, the unheld-gate control,
source hashes and the exact generated C-source transformations. Reproduce from the
microcode directory with `python3 g2/receiver_timer1_offset_handoff.py`.
