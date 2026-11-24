# Interval-weighted events feed controller output flags

The controller has a concrete path from external-interrupt-1 events to RAM
30.2 and 31.4, two bits in the outgoing four-byte buffer. The interrupt handler
updates byte 6E from a countdown; polling routine 1790 interprets that byte,
sets or clears those output bits, and controls event re-enabling. Byte 6E also
feeds the [input decoder](DECODE.md).

This identifies firmware behavior, not the physical event source. A carrier or
frequency qualification role is plausible, but the input signal and clock rate
are not established. No waveform, baud rate, or DSC2847 connection is inferred.

## Countdown and interrupt accumulation

The vector at 0013 saves PSW and A, then jumps to 1760. The timer-1 handler at
07D7 selects register bank 2 and decrements the R3:R2 pair, RAM 13:12. The
external-interrupt handler uses that pair and finally resets it to FFFF.

Let H/L be RAM 13/12 and S be byte 6E on entry. The handler adds a weight only
when all three conditions hold:

- S has bit 7 clear.
- H is FF.
- L is in BD–F2 inclusive.

The added weight is `floor((256-L)/4)`, ranging from 3 to 16. Addition wraps
modulo 256. If the countdown began at FFFF and only the timer handler changed
it, this corresponds to 13–66 decrements since reset, weighted as
`floor((decrements+1)/4)`. These are countdown ticks, not an established duration.

Whether or not a weight is added, the handler resets H/L to FFFF, enables the
timer-1 interrupt bit, disables the external-interrupt-1 enable bit, restores
A/PSW, and returns with RETI. Bit 7 of S therefore inhibits further accumulation
until another firmware path clears it.

## Polling, re-enabling, and output updates

Routine 1790 has two entry cases:

- If H=FF and L>=60, it proceeds to qualification. It enables external interrupt
  1 when L<FB, but leaves that enable bit unchanged for L>=FB. Starting after
  the event handler, this can defer re-enabling until five countdown decrements.
- Otherwise it enables external interrupt 1, masks S with 3F, and clears RAM
  30.2 and 31.4. If state byte 34 is zero, it also clears RAM 22.5. If byte 34
  is zero or H<D9, it resets S to zero, reloads H/L with D8F0, enables timer 1,
  and returns. Otherwise it continues into qualification with the masked S.

Qualification applies this table:

| S before qualification | Result |
| --- | --- |
| 00–27 | Preserve S and the current output bits |
| 28–3E | Set S=BF and set RAM 30.2 and 31.4 |
| 3F–66 | Preserve S and the current output bits |
| 67–7F | Set S=FF and set RAM 30.2 and 31.4 |
| 80–FF | Preserve S and the current output bits |

All table values are hexadecimal. In particular, a call may clear the output
bits, mask S, and then immediately set the bits again. Treating the initial
clear as the final result would misdescribe the routine.

The existing serial-output routine sends RAM 30 first and RAM 31 second, with
XOR masks 00 and 03 respectively. Those masks preserve bit 2 of the first byte
and bit 4 of the second. Later firmware may modify the output buffer before a
transfer; the study does not claim these local output writes always survive
unchanged to a physical pin. Similarly, FF in byte 6E is the value tested by
0620's state-selection logic, but the full main-loop state machine is not yet
reconstructed.

## Validation

[Reference functions](../controller_event.py) describe the accumulator and
polling transition. [Configuration](../controller-event-scenario.json)
provides the local states. The probe enters the real interrupt vector at 0013
or the real polling routine at 1790, with a return frame and global interrupts
disabled. It supplies countdown values directly; it does not synthesize a
physical input waveform.

The 30,436 ROM/reference comparisons include:

- All 256 low-countdown values with three high bytes and eleven accumulator
  values at thresholds and boundaries, for both routines.
- All 256 high bytes with ten boundary low values and zero/nonzero mode byte 34.
- Output-byte patterns that check setting, clearing, and preservation of the
  unrelated bits.
- Several initial interrupt-enable patterns, always with global enable clear,
  to check that unrelated enables survive.

Every case checks all 128 internal-RAM bytes, the interrupt-enable register,
return PC, stack pointer, and absence of emulator exceptions. The suite executes
all 27 instruction starts in the vector/interrupt path and all 41 in the
polling routine. This is bounded state testing, not exhaustive coverage of all
possible simultaneous input states or hardware timing.

```sh
python3 nokia/data-modem-2400-2400/analysis/controller_event_study.py
```

[Report](../results/controller-event-study/report.json) preserves source and
ROM hashes, fixture/execution digests, instruction coverage, and 38 complete
state witnesses. Raw ROM and the CPU core are unchanged. The physical input
and output identities remain open requirements of the microcode plan.
