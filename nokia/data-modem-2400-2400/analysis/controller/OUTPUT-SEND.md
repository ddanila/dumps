# Output construction through transmission in the actual caller

Entry 1EE2 executes the ROM's LCALL 006E, returns, executes LCALL 0899, and
stops at 1EE8 before the next main-loop helper. There is no PC redirection,
intermediate state injection, or modified ROM. This joins the output builders,
subsequent setup operations, and four-byte shift-chain transmission.

The [study](../controller_output_send_study.py) composes the previously
verified output and peripheral-programming references. In all 32,768 cases:

- RAM30–33 retain the values from the construction/override reference.
- The transmitted bytes are RAM30, RAM31 XOR 03, RAM32, RAM33 XOR F8.
- Counters 49/4A/65 and patterns 3D/3E retain the reference updates.
- Mode byte RAM35 follows the received RAM2D selection documented in
  [peripheral programming](PROGRAM.md).
- A changed RAM35 programs control port 06. If RAM35 is unchanged, state
  RAM34 is zero, and flag RAM24.5 is set, control port 05 is programmed first,
  then port 06. Otherwise no programming occurs. The changed-mode branch
  skips the control-port-05 programming even in state zero.
- Four synthetic transmit completions precede the final P1.2 latch pulse;
  the pulse is then cleared. The serial routine clears P1 bits 0 and 2 on
  entry and otherwise preserves the output construction's final pin values.

These observations separate external USART programming from the controller's
own serial shift-chain output. The latter transmits the four output bytes;
the former sends mode/control bytes through MOVX. Neither interface is yet
identified as a verified DSP input channel.

## Local assumptions and coverage

The [scenario](../controller-output-send-scenario.json) keeps global
interrupts disabled, bank zero at entry, and supplies a completion event eight
emulator ticks after each SBUF write. All unseeded RAM starts at zero. P2
retains its reset value FF, so the logged addresses are **FF05/FF06**, not
0005/0006. Actual peripheral address decoding is outside this local model.

There are 128 seeded fixtures for every state byte. Half start with RAM35
already equal to the selected mode; the other half use a random prior mode.
Flags, payload, four prior outputs, three counters, and both pattern bytes
vary independently. The sweep visits 602 instruction starts and stores 85
witnesses in the [report](../results/controller-output-send-study/report.json).
All 397 reachable instructions in the previously checked construction prefix
are covered, as are both programming decisions and all setup helpers called
in these cases.

This comparison checks selected application state and the complete external
write/serial event values, stop PC/SP, P1/P2, and final serial scratch byte.
It does **not** compare every internal initialization flag, timer, register,
or stack residue against a separate reference. The report explicitly lists
five unvisited instructions in the output tail: 04C0, 04C2, 04D8, 04DA, 04ED.
These paths require timer state absent from this zero-initialized fixture.
The timer-interrupt body beginning at 078E is not entered by the direct call
to 077C; it is not counted as covered initialization code.

```sh
python3 nokia/data-modem-2400-2400/analysis/controller_output_send_study.py
```

The report includes source and ROM hashes and deterministic fixture/execution
digests. This is a complete execution of the output-and-transmit portion of
the main loop under the stated assumptions, not a complete polling iteration,
physical timing reconstruction, or proof that the modem processes a signal.
