# Controller bytes can change a table operand in a diagnostic route

The [D349 source candidate](PHOTO-TABLE-SOURCE-UPDATE.md) used constant test
bytes. This [follow-up execution](photo_table_controller_source.py) offers the
**unchanged 8031 main-loop USART-01 output bytes** to D at instruction `349`,
one byte per visit. It retains the same photo-pin candidates, q1/q3 mappings,
previous-ALU-Y table dispatch, saved branch seeds and diagnostic AC=RST pulses
at `084`. The controller-to-D349 connection and restart command are still
untraced hypotheses.

Across four controller streams and seeds 22, 116, 184 and 245, **32 runs**
finish cleanly. They make 56 visits to `349` and 264 reached 3C5/3DA table
calls. Every table result obeys the [exact sign formula](PHOTO-TABLE-EXACT.md).

| Mapping | D349 behavior | Source high byte seen by later table calls |
| --- | --- | --- |
| q1 | R5 receives `01` for every offered byte | `00` or fixed `01` |
| q3 | R5 receives `D+1` for the used controller bytes | `00`, or values derived from the stream |

For seed 116 with controller selector `20`, the first two bytes are `E7,7B`.
The two D349 visits write `E8,7C` to R5. Later sign-table calls use source
high byte `7C`, making the exact table output controller-dependent under this
candidate route. Seed 184 exposes its first byte in two earlier calls; a
later R5 write elsewhere clears the source before its remaining calls. That
last-writer effect matters when assessing the route.

The tested output candidates `392` and `39E` do not complete a transmitter
chain: `392` is not reached, and all **40 visits to `39E`** have ALU output
`00`. None occurs after the final D349 update of its run. Each run consumes
only one to three of the available controller bytes and eventually returns
to the `084` wait. Thus a changing table operand is established only inside
this conditional execution, with no sustained controller-fed line signal.

A dynamic register-flow check makes the gap more precise. The 264 calls write
R10–R13 **1,056 times**. For each run, the checker follows every such value
until another instruction replaces it, and uses the executed Am2901 source
selector plus the `Y=A` destination case to detect reads. It finds **zero
reads of table-written output registers** in all 32 traces. The varying ALU
values at other PCs therefore do not demonstrate use of these table results
in this fixture. This does not prove the tables are unused in other control
paths or under the board's real wiring.

The [report](results/photo-table-controller-source.json) records the exact
offered bytes, D349 writes, table-call sources and outputs, candidate output
visits, trace digests and source hashes. The next experiment must find an
input scheduling or microcode path that keeps consuming controller data **and**
reaches a changing DAC-bound code after table evaluation. Further candidate
connections can be tested with the current photographs. A useful branch or
timing candidate must first reach a consumer of R10–R13 after a table call.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/photo_table_controller_source.py
```
