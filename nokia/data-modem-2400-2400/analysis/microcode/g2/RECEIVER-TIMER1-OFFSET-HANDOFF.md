# Timer 1 interrupts during the offset-PROM receive handoff

The [offset-PROM zero-run handoff](RECEIVER-MASK04-MARGIN-ZERO-HANDOFF.md)
reaches controller state `B0` with exact line bytes, but its paced 8031
probe disables Timer 1. This [replay](receiver_timer1_offset_handoff.py)
enables the same emulator Timer 1 configuration used by the earlier
[interrupt-paced controller run](MAIN-LOOP-TIMER1-SEGMENT2.md):
`TMOD=15`, `TH1=FC`, `TL1=21`, `TCON=40`, `IE=88`. It keeps the saved
real-PROM line bytes, 416 modeled 8031 ticks per RxC bit, initial `AF`
state, synthetic DTE input and narrow external SYNDET/8251A model
unchanged. A separately compiled timer-disabled probe
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

The zero-initialized **unheld-RAM15 control** keeps Timer 1 active and
uses the aligned pulse, but no longer forces RAM15 positive at state
dispatch. In both delays it falls to state `00`, consumes no receive
bytes, and records seven USART overruns while eight characters complete.
The ROM explains why: Timer 1's ISR at `07D7–07F8` selects register bank 2
and decrements `R5:R4`, which occupy RAM15:RAM14. Starting both at zero
underflows the high byte to `FF` on the first interrupt. The state
dispatcher at `1024–1029` treats that negative high byte as a reason to
clear the state.

The unchanged ROM contains `MOV 15h,#75h; MOV 14h,#30h` at `04B1`, `117C`,
`1396` and `1476`. A third probe seeds that **ROM-literal `75:30` countdown
once at the synthetic `AF` entry**, then removes the per-dispatch RAM15
force. Both delays consume eight exact bytes without overrun, decode eight
zeros and reach `B0` after 57 Timer 1 interrupts. Their final
RAM15:RAM14 is `74:F7`, exactly the expected countdown after 57
decrements; `B0` occurs at ticks 53,253 and 53,243. Thus a one-time
positive countdown is sufficient for this 57 ms handoff, and the
zero-seeded failure does not imply the physical board needs a continuously
forced gate.

The probe still starts from a preserved synthetic `AF` state. The ROM
literal's **actual inheritance path into `AF` is not yet shown**; another
routine could reset or alter the countdown before that state. DTE input,
mode-0 serial completion, RxD/RxC/SYNDET route and pulse source remain
assumed; DSC and 8031 execute sequentially. C3 stays open. Next execute
the preceding state transition into `AF` and inspect RAM15:RAM14 there,
then test the sync event without placing it directly while retaining the
same PROM receive data and early/late controls.

The [machine report](results/receiver-timer1-offset-handoff.json)
includes all byte timings, ISR counts, frames, zero and ROM-literal seed
controls, source hashes and the exact generated C-source transformations. Reproduce from the
microcode directory with `python3 g2/receiver_timer1_offset_handoff.py`.
