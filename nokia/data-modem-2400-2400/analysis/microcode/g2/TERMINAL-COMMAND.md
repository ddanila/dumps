# An explicit 8X02 command hypothesis at the 084 tail

The existing [terminal-tail study](../assumed/TERMINAL-TAIL.md) shows that
lowering TEST at 084 is not a general release: fallthrough executes 085–089,
and POP at 089 encounters an unknown stack entry on the empty-stack reset
path. A different possibility is an external change of the 8X02 AC command
pins. The [Signetics 8X02 specification](https://bms.isjtr.ro/other/sos/Philips_elcoma_Signetics_Bipolar%26MOSMicroprocessors_1978.pdf)
lists AC=111 as **RST**, which sets the next address to zero without changing
the stack pointer. Its 28-pin diagram has no runtime RESET input; EN controls
the address output buffer. Neither the photos nor the current net ledger
establish an external command override on this board.

The [probe](terminal_command_probe.py) tests this as a **counterfactual wiring
and timing hypothesis**. It starts with the saved q3 lower-bank Gray-operand
fixture, runs the actual four PROMs and modeled datapath continuously, and
substitutes the chip's AC=111 operation for the decoded BRT at the first 15
arrivals at 084. The override changes no PC directly and clears neither RAM,
Q nor the circular stack. On the sixteenth arrival, the ordinary 084
self-branch resumes. A held D316 byte is compared with a four-byte sequence;
these input bytes and the ROM gate remain diagnostic assumptions.

| D316 fixture | AC=RST events | ROM reads at 317 | Candidate Y at 392 |
| --- | ---: | ---: | --- |
| Held 119 | 15 | 11 | 10, 10, 10, 10, 10, 10 |
| 119, 120, 121, 122 repeating | 15 | 11 | 10, 34, 10, 34, 10, 34 |

Both 1,900-instruction runs complete without modeled stack error. The 16
arrivals at 084 occur at cycles 110, 231, 351, 458, then with the same
121/120/107-cycle pattern repeated. The six 392 visits are exactly 348 cycles
apart. The changing input does affect this candidate ALU value, but only two
values appear, and many passes do not visit 392 at all. The ROM addresses in
the changing run are 07C, 07C, 07E, 07E, repeating; the held input alternates
07C and 07B on successive reads. This is a consequence of retained datapath
state, not a demonstrated differential phase accumulator or line signal.

At each injected command, the modeled logical stack is balanced and the
physical stack pointer is zero. The four-entry stack's old contents remain
present, as the real RST command requires. This diagnostic does not show that
the board can issue AC=111 at 084, that the pulse can be tied to a sample
clock or controller event, or that 392 drives the analog output. It narrows
one plausible continuation: even with this clean restart, the saved q3
fixture does not pass G2's transmitter check. Other field mappings and input
or output routes remain open; there is no goal blocker.

The [report](results/terminal-command-probe.json) records every restart
cycle, live stack, ROM read, candidate output and source hash. Reproduce it
with:

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/terminal_command_probe.py
```
