# ROM-gate predictions across eight handlers

The [ROM-gate search](ROM-GATE.md) found 137 predicates that preserved selected
sine-path outputs. Applying those same gates to other input-selected handlers,
without retuning their replies, separates four classes of control-flow behavior.
No gate causes a stack fault in this experiment, but matching the original
sine output does not ensure the same wait or completion behavior elsewhere.

## Unchanged comparison inputs

Every run starts at 000 with zero RAM/Q under q3 and previous flags. Inputs at
002/076 accumulate Q=0 through 7, selecting each of the eight handlers at 109.
Early replies remain `[1,0]` at 117/106. Other D values are 1, and non-109
dispatches use index 2. There is no special phase input at 316, independent
component input at 317, preceding-Y selector at 38F, or zero reply at 36D.

Each of the 137 fitted gates is applied to all its qualifying control words,
using upper-bank ROM addressed by preceding Y. Eight baseline runs retain
external inputs everywhere. Neither the gate terms nor the conditions are
changed to improve a particular handler's outcome. This tests transfer beyond
the fitted sine scenario, not independent hardware observations.

## Results

The 1,096 gated runs have 819 terminal outcomes and 277 persistent modeled
loops. All complete 512 cycles cleanly, with no unused words. Repetition is
proved using the full registers/flags/stack/input-phase state, including Y for
ROM-address feedback; it is not inferred from the final PC alone. There are
no unresolved bounded or model-error outcomes in this sweep.

| Gate count | Handler 2 (18B) | Handler 5 (345) |
| --- | --- | --- |
| 91 | Repeats | Terminal |
| 24 | Repeats | Repeats |
| 21 | Terminal | Terminal |
| 1 | Terminal | Repeats |

All gates agree on the other six outcome classifications: handler 0 repeats;
handlers 1, 3, 4, 6 and 7 reach 084. This table compares classes, not full
execution equivalence. The report also compares complete final register/stack
states and normalizes the retained Y field for the non-ROM baselines.

Thus 25 gates introduce a handler-5 wait relative to the baseline, while 22
make handler 2 terminate. These changes are not a hardware-correctness score.
For example, gate 8 (`10.3=0 AND 11.7=1 AND 17.6=0`) supplies ROM zero at 19B,
so 19C prepares R4=FF instead of FE. The unchanged external byte 1 then satisfies
the 1EC comparison. Termination here reflects a changed comparison value,
not discovery of a real external acknowledgement.

## The two-bit gate creates a ROM/carry feedback loop

The two-bit gate `11.4=0 AND 18.5=0` belongs to the 24-gate class: handler 2
still polls, and handler 5 acquires a three-instruction wait at 36C–36E. On
entry, R0=FF. Its stable iteration is:

| Instruction | D source/value | Result and exposed Y | Control effect |
| --- | --- | --- | --- |
| 36C | ROM[100]=0 | R1=FF, carry=0; Y=FF | Push loop frame |
| 36D | External 1 | R2=00, carry=1; Y=old R1=FF | Continue |
| 36E | External 1 | R3=01, carry=0; Y=old R2=00 | Previous carry=1 repeats |

The next ROM address is 100 because 36E exposes **R2 on Y**, not its arithmetic
result 01. This distinction closes the feedback loop: every next 36C reads
zero again. The state repeats exactly every three instructions. This extends
the [carry-chain interpretation](CARRY-CHAIN.md) with an actual modeled ROM
feedback mechanism rather than a constant-D local fixture.

Changing only the 36D reply to zero releases the loop. Three separate controls
supply zero immediately or after one or seven reads of 1. Their traces before
the first 36D read match the held-input gate run exactly. Each failed reply adds
three instructions, and the first 084 cycle is respectively 110, 113 or 131.
No return address, PC, stack frame, or register is injected.

The earlier sine scenario already supplied zero at 36D, so it could not expose
this difference. Gate 50 (`11.3=1 AND 17.3=1 AND 18.1=0`) leaves 36C external
and reaches 084 with the original default replies. Both gates still fit the
same read-selection labels and pass the sine-output checks.

## Artifacts and scope

[Configuration](rom-gate-handlers.json), [runner](rom_gate_handlers.py), and
[report](results/rom-gate-handlers/report.json) retain all 1,096 gate/handler
results, eight baselines, three delayed-reply controls, and twelve full
witness traces. Source hashes cover the search and execution code. All artifacts
reproduce byte for byte. The 95-test suite checks the new three-cycle recurrence,
the F-versus-Y distinction, competing gate behavior and delayed release timing.

Only input sums 0–7 are swept here; each handler's other 31 selector aliases
and different captured inputs remain outside this experiment. Physical read
selection, peripheral acknowledgement, DAC writes and sample timing remain
unresolved. No new gate becomes an emulator default or a recovered field.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/rom_gate_handlers.py --out /tmp/nokia-rom-gate-handlers
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -p 'test_*.py'
```
