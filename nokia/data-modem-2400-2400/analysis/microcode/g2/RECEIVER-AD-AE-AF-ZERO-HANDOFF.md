# Timer-paced `AD→AE→AF→B0` receive handoff

The [earlier handoff](RECEIVER-AE-AF-ZERO-HANDOFF.md) began at synthetic
`AE` with both the long and short countdowns seeded. This
[replay](receiver_ad_ae_af_zero_handoff.py) begins one state earlier, at
`AD`, seeds only the ROM-literal long countdown RAM15:RAM14=`75:30`, and
lets the ROM load the short timer. Timer 1 runs throughout, with no
per-dispatch countdown force. The DTE command byte `02` is read by the ROM
and decoded to RAM2A mode `05`.

The `AD` dispatch-table entry reaches `1220–1229`, which tests RAM64
against eight. In both scrambler-delay fixtures, RAM64 reaches eight and
the ROM increments state `AD→AE` at modeled tick 6,990/6,996. The long
countdown is then `75:2A`, after six Timer 1 interrupts. The `AE` handler
loads its `00:32` short timer once. After 58 total interrupts the ROM
increments `AE→AF` at tick 58,399/58,576 with the long countdown still
positive at `74:F6`.

The assumed RxC stream begins at tick 85,000, with one bit every 416
modeled 8031 ticks. Eight receive bytes are taken from saved real-PROM
±7 Hz traces through the frozen conditional readout. The replay tests an
external SYNDET pulse at bit 63, 64 or 65, no pulse, an opposite DTE
selector and a mode-`00` control:

| Scrambler delay | Aligned bit 64 | Early bit 63 | Late bit 65 | No pulse | Opposite selector | Mode `00` |
| --- | --- | --- | --- | --- | --- | --- |
| 5 | `B0` at tick 138,849; eight zeros | `AF`; five zeros | `AF`; four zeros | `AF`; zero | `AF` | `AE` |
| 18 | `B0` at tick 138,209; eight zeros | `AF`; five zeros | `AF`; four zeros | `AF`; zero | `AF` | `AE` |

Both aligned runs consume the exact eight PROM-derived line bytes without
emulator errors or receive overruns. Each executes 141 Timer 1 interrupts;
RAM15:RAM14 finishes at `74:A3`. This shows that the `AD→AE→AF→B0`
controller path can run with a short timer loaded by the ROM itself and a
single inherited long-countdown value.

The `AD` start, `75:30` long-countdown seed, DTE completion, RxD/RxC and
SYNDET circuitry, ADC capture and external readout are still assumptions.
The DSC PROM and 8031 portions run sequentially, so this does not prove
the physical receive route or close C3. Next trace how the controller
enters `AD` and loads its long countdown, then challenge a photo-compatible
sync/serial route with the same controls. Missing continuity is not a
prerequisite for those experiments.

The [machine report](results/receiver-ad-ae-af-zero-handoff.json) records
the cases, byte streams, state-edge timings and source hashes. Reproduce
from the microcode directory with
`python3 g2/receiver_ad_ae_af_zero_handoff.py`.
