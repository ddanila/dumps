# Direct destination bytes under q3

The q3 mapping supports a diagnostic path from a nested input load to two
independently addressed internal register stores. Unlike the q2
[register contract](REGISTER-CONTRACT.md), it does not require adjusting the
second destination byte after storing into R6. This distinguishes the mappings
by observable internal state; it does not identify a physical controller port.

## Reset and input contract

Start from the [masked nested dispatch](MASKED-NESTED-DISPATCH.md) A3 witness:
zero initial RAM/Q, seed 115, external bytes at 2E0/2E1 whose AND is A3, and
Q-derived indices at 21F and 2C4. The real four-entry stack reaches 225 at cycle
188. The replayed prefix is identical to the saved witness. No return frame,
register contents or entry PC is invented.

Change only these later inputs and index sources:

- At 225 supply payload `u`, which loads Q.
- At the two visits to 089 supply destination numbers `a` and `b`, each 0–15.
- At 07E and 081 use preceding ALU Y as the dispatch index.

Under q3, 089 computes `D - 0` with carry-in one, exposing D unchanged.
The 08A–099 table copies R0 to the selected register and returns. Each store
therefore writes `v = u >> 1`. The stores execute at cycles 218 and 227;
084 is first reached at cycle 230. Q remains u, maximum stack depth is four,
and final stack depth is zero. These are modeled instruction counts, not a
physical sample rate.

## Full register effects

For the fixed default external byte `d=CC` and this reset prefix, start with
its checkpoint RAM and apply the following updates, modulo 256:

1. The q3 28E–295 path writes `R3=d+u`, `R0=u`, and `R15=u-d+1`.
   This differs from the q1/q2/q4 affine interpretation.
2. 07C and 07E write `R2=d+u` before the first indexed store.
3. Before each store the helper writes `R0=v` and
   `R5=((d-u-1)&FF)>>1`.
4. Write v to register a, run the helper again, then write v to register b.

All other checkpoint registers survive unless selected by a store. A first
store to R5 is overwritten by the second helper unless the second store also
selects R5. This loses the first stored value in 3,840 cases. A first store to
R6 leaves the second address unchanged in all 4,096 corresponding cases.
For example, `u=1, a=6, b=7` uses destination bytes `06,07` and stores zero
in R6/R7. The q2 contract requires `D1,07` from its checkpoint instead.

## Validation and scope

The study restores the freshly replayed checkpoint and exhausts all
65,536 combinations of payload and two destinations. Every continuation
matches the independently stated full-RAM formula, preserves Q, and reaches
084 after 42 further instructions. Eight complete 512-cycle core runs match
every restored continuation step, including flags, input bytes, dispatch
indices, stack slots, and final state. Tests also reject reuse of the q2
address construction as a q3 destination contract.

The prefix-capture and continuation machinery is shared with the q2 study;
its optional explicit read bytes leave the original q2 behavior unchanged.
The q2 exhaustive study is replayed separately as a regression check.

Earlier dispatches still include seeded scenario choices. External reads are
PC-keyed stubs, and preceding-Y dispatch remains hypothetical. The result is
an input-to-internal-storage contract under q3, not an established board bus
protocol, DAC write, or modem algorithm.

Reproduce from the repository root:

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/q3_register_contract.py
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -p 'test_assumed.py'
```

[Configuration](q3-register-contract.json),
[exhaustive report and full witnesses](results/q3-register-contract/report.json).
