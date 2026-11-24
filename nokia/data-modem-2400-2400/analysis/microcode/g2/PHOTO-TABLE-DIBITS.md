# Controller dibits through the reached sign tables

The [exact table rule](PHOTO-TABLE-EXACT.md) identifies the four sign choices
made by 3C5 and 3DA under the held photo-pin candidate. The earlier
reset-reached calls used scenario-selected table entries. This
[execution screen](photo_table_controller_dibits.py) replaces **only those two
table indices** with the previous Am2901 Y value, then offers dibits from
four byte streams written by the unchanged 8031 main loop to USART 01.

The bytes are expanded least-significant bit first; adjacent bits form a
low-two-bit D value. Each dibit is offered at `3D6` or `3C1`, immediately
before its computed call at `3D7` or `3C2`. A D=0 baseline determines the
chronological call order for each scenario seed; the run verifies that its
dibit-driven calls retain that order. The other computed dispatches and
branch conditions remain the saved rotation-study scenario. This is a
candidate serialization and branch-bus route, **not** a traced controller
connection.

| Photo-compatible mapping | Reached calls | Predecessor Y for D=0,1,2,3 | Selected table entry | Direct dibit matches |
| --- | ---: | --- | --- | ---: |
| q1 | 28 | 0,1,2,3 | 0,1,2,3 | 28/28 |
| q2 | 28 | FF,FF,FF,FF | 3,3,3,3 | 10/28 |
| q3 | 28 | 0,1,2,3 | 0,1,2,3 | 28/28 |
| q4 | 28 | FF,FF,FF,FF | 3,3,3,3 | 10/28 |
| fitted-swapped | 28 | FF,FF,FF,FF | 3,3,3,3 | 10/28 |

These are eight executions per mapping: four distinct 8031 line-side streams
under two saved branch-scenario seeds. All **40 runs complete**, make **140
calls**, and return to the `084` wait loop by 300 instructions. Every table
write matches the high-byte sign formula. The q2/q4/fitted matches occur only
when the offered dibit happens to be 3; their table choice does not respond
to the dibit in this route.

For q3, seed 14 and controller stream `20`, the first five offered dibits are
`3,1,2,3,3`; the reached entries are exactly `3,1,2,3,3`. With source pair
`(0000,FF00)`, the output pairs are `(0000,FFFF)`, `(0000,0001)`,
`(0000,0001)`, `(0000,FFFF)`, `(0000,FFFF)`. This establishes a
**controller-data-dependent sign selection in the declared emulator
fixture**. It favors q1/q3 over q2/q4/fitted for this particular candidate
input and dispatch wiring.

It does not yet establish DPSK modulation. The USART-to-D route, two-bits-per-
call timing, previous-Y connection to U9's branch bus, held E4/E2 levels,
upstream scenario dispatch, source-pair initialization and DAC08 route are all
unverified. The executed path makes at most five table calls per run, then
parks at `084`; its outputs show no continuing carrier or pulse shaping. The
[diagnostic RST continuation](PHOTO-TABLE-RESTART.md) repeats those calls with
retained RAM/Q and still finds one fixed source pair per run. The
[report](results/photo-table-controller-dibits.json) records every offered
dibit, predecessor ALU value, selected entry, source and output pair, plus
the controller and microcode source hashes.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/photo_table_controller_dibits.py
```
