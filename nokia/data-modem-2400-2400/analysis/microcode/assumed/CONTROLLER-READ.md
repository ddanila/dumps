# The repeated external read discards its returned byte

The helper at controller address 08DD performs a real MOVX read in the emulator,
but its returned data is overwritten before use in the three observed caller
continuations. The read bus cycle may still have an external side effect.
Calling it a consumed status or sample byte would overstate the evidence.

## Read helper and address selection

The unchanged ROM executes:

```
08DD  CLR  P2.5
08DF  SETB P2.7
08E1  CLR  P2.6
08E3  MOV  R0,#04
08E5  MOVX A,@R0
08E6  CLR  P2.7
08E8  RET
```

Using the same P2-high-byte convention as the existing controller harness,
the read address is `(((initial_P2 & 1F) | 80) << 8) | 04`. With P2's low
five bits zero, this is 8004, matching the recorded reset-started executions.
The helper preserves those low five bits and leaves bits 5, 6 and 7 clear.
It does not force the low five bits to zero itself.

The local probe tests all 256 read values at P2=00 and all 256 initial P2
latch values with read value A5, separately. In the helper-only runs, A returns
the supplied byte unchanged. This positive control verifies that subsequent
insensitivity is caused by firmware execution, not a callback ignoring input.

## Where the byte is lost

Direct LCALL/ACALL decoding at instruction addresses in the saved preseeded
controller trace finds three observed callers:

| Call site | Continuation | Equality checkpoint |
| --- | --- | --- |
| 1E37 | 1E3A loads A from timer RAM byte 17 | 1E3C, before its timer-bit test |
| 1E72 | 1E75 loads A from timer RAM byte 17 | 1E77, before its timer-bit test |
| 1ED3 | 1ED6 calls serial-input routine 0800; 081B loads A from normalized input byte 20 | 081D, before comparison with prior input |

The first two are initialization-loop paths. The third occurs on every
ordinary polling iteration: the raw `80 E6` instruction at 1EEB branches back
to 1ED3, not just to the serial-input call at 1ED6.

Each continuation is run with every possible returned read byte while all
other inputs are fixed. At each checkpoint, the 256 executions agree in PC,
SP, all 128 internal-RAM bytes, all 128 SFR bytes, and elapsed harness ticks.
This includes A and PSW/parity, rather than comparing only a selected output.
The example timer byte is 12, and the example first normalized serial byte is
15 (hex); those values replace A regardless of the external read byte.

The address-selection sweep also executes these callers and checks the
selected bus address, final P2 and expected accumulator value. Together with
the helper-only controls, this totals 2,048 local probes and 768 full-state
comparisons across varying returned bytes. All checks pass.

## Interpretation and limits

The result narrows the interface question: an emulator connection that maps
this read byte directly into a consumed DSP status or sample value would need
evidence beyond these callers. A read-triggered external action remains
possible. The repeated access could serve some control or maintenance purpose,
but neither an acknowledgement, watchdog service, reset pulse nor a particular
board connection has been identified.

These are local executions with interrupts disabled and synthetic serial
completion events. Only callers observed in the selected reset trace are
classified; unseen entry paths are not excluded. The callback models the
returned byte and address, not side effects inside the physical device. No
read is removed from the controller emulator, and no DSP bridge is added.

## Reproduce

```sh
python3 nokia/data-modem-2400-2400/analysis/controller_read_study.py \
  --out /tmp/nokia-controller-read
python3 nokia/data-modem-2400-2400/analysis/interface_study.py \
  --out /tmp/nokia-controller-interface
```

[Configuration](../../controller-read-scenario.json) and the
[report](../../results/controller-read-study/report.json) preserve the observed
callers, polling back edge, local assumptions, source hashes, execution digest
and 12 event/state witnesses. The shared [C probe](../../interface_probe.c)
is extended without changing its earlier input/output-frame behavior: all
4,362 prior interface fixtures pass with identical execution digest and
witnesses. Both reports reproduce byte for byte, and all 61 microcode tests
pass. Physical I/O identification remains an open requirement of the plan.
