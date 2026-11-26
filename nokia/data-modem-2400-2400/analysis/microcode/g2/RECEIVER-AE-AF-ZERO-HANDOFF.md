# Timer-paced `AE→AF→B0` receive handoff

The earlier [Timer 1 handoff](RECEIVER-TIMER1-OFFSET-HANDOFF.md) began in
synthetic controller state `AF`. This replay begins in `AE` and lets the
preserved 8031 ROM execute both state transitions. It seeds RAM15:RAM14
once with the ROM's `75:30` long-countdown literal and RAM17:RAM16 with
its `00:32` short-timer literal. Timer 1 remains enabled; no per-dispatch
RAM15 force is used.

The ROM reads the second synthetic DTE byte at `0813–0823`, XORs it with
`07`, and writes the result to RAM2A. The [mode probe](receiver_ae_to_af_timer_probe.py)
varies that byte and observes the `AE` handler at `12EA–130C`:

| DTE byte | ROM-decoded RAM2A | `AE` visits | Short reloads | `AF` entry |
| --- | --- | ---: | ---: | --- |
| `07` | `00` | 66 | 66 | None |
| `06` | `01` | 66 | 66 | None |
| `03` | `04` | 66 | 66 | None |
| `02` | `05` | 60 | 0 | Tick 51,607 |

In mode `05`, the ROM reaches `AF` after 51 Timer 1 interrupts with
RAM15:RAM14 still positive at `74:FD`. The `AE` path checks the short
timer and executes its state increment once. The other modes keep
reloading that timer and stay in `AE` for the tested run. This establishes
a ROM-executed entry into `AF` under this fixture; the start at `AE` and
the countdown seeds are still assumed.

The [continuous handoff replay](receiver_ae_af_zero_handoff.py) delays the
assumed 416-tick RxC stream to tick 51,200. Mode `05` reaches `AF` at
tick 51,607 or 51,788, before the first data-bit edge at tick 77,824.
For each scrambler delay it supplies eight bytes recovered from a saved
real-PROM ±7 Hz trace and varies only the external SYNDET pulse or DTE
selector. Each run executes 108 Timer 1 interrupts.

| Scrambler delay | Aligned pulse at bit 64 | Early bit 63 | Late bit 65 | No pulse | Opposite selector | Mode `00` |
| --- | --- | --- | --- | --- | --- | --- |
| 5 | `B0`, eight zero octets, tick 104,652 | `AF` | `AF` | `AF` | `AF` | `AE` |
| 18 | `B0`, eight zero octets, tick 104,813 | `AF` | `AF` | `AF` | `AF` | `AE` |

Both aligned runs consume their exact eight line bytes without emulator
errors or receive overruns and finish with RAM15:RAM14=`74:C4`. The early
and late controls consume only five and four zero octets respectively;
neither crosses the eight-zero threshold.

This is a conditional controller behavior. The `AE` start, countdown
initialization, DTE frame, serial completion, RxD/RxC/SYNDET source and
timing, ADC capture and external dibit consumer have not been established
as physical Nokia connections. The DSC PROM trace and 8031 receive replay
are sequential, not one concurrent board simulation. C3 remains open.
Next run a preceding controller state into `AE` with inherited countdown,
then test a photo-compatible SYNDET decoder and serial path against the
same early/late controls. Missing continuity does not block those tests.

Machine reports: [mode screen](results/receiver-ae-to-af-timer-probe.json)
and [zero handoff](results/receiver-ae-af-zero-handoff.json). Reproduce from
the microcode directory with `python3 g2/receiver_ae_to_af_timer_probe.py`
and `python3 g2/receiver_ae_af_zero_handoff.py`.
