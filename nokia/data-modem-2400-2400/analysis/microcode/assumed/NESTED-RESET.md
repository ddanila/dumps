# The nested ROM wrapper executes from zero reset

The q2 wrapper at 2BC–2C5 has clean integrated reset witnesses under the
existing scoped dispatch tables, without an optional BRT gate. This connects
the [local arithmetic interpretation](NESTED-PREPARE.md) to an actual
reset-driven calling context. It still does not identify the physical dispatch
index or an external protocol.

## A fixed sweep with real flags

The experiment runs seeds 0–4095 for 512 cycles each. Each starts at 000 with
zero RAM and Q. Conditions use the existing previous-ALU-flag policy, including
its fixed condition stubs; conditions are not randomized. Dispatch entries
are seeded random choices from the existing declared tables. Input D is
`(73*seed+1) mod 256`, with diagnostic D-then-zero replies at the early waits
117 and 106. Every other read supplies D.

| Observation | Result |
| --- | --- |
| Clean runs | 4,096 of 4,096 |
| Executed cycles | 2,097,152 across separate 512-cycle runs |
| Runs ending at terminal 084 | 2,840 |
| Other bounded outcomes | 1,256; not classified as permanent loops |
| Distinct used words across the sweep | 718 |
| Runs visiting outer call 21F | 277 |
| Runs entering and returning from 2BC | 5 |
| Nested targets in those five runs | 225 four times; 2B3 once |

All five nested runs reach 084 within the bound. They are seeds 115, 501,
2855, 3519 and 3614, with D=CC, DE, 20, 78 and 8F respectively. In all five,
Q and R5 are zero on entry to the wrapper. This is a bounded observation,
not proof that nonzero entry states are impossible from reset. The broader
nonzero local fixtures remain separate evidence.

The 718-word union is integrated q2 coverage over multiple scenarios and
seeds. It is not merged with the 941-word sequencer-only sweep or used to
change the default graph's 999-word reachability result.

## First witness: input CC passes through the nested leaf

Seed 115 enters 21F at cycle 176. The existing ROM interpretation selects
entry 81: byte D1=BC plus bank 200 yields target 2BC. Its incoming Q=0 was
last written by 2F3 at cycle 163. R5 is also zero. The prefix prepares:

- R0=00, from Q shifted right;
- R2=CC, from D+Q;
- R4=66, from the wrapped D+Q sum shifted right.

At cycle 185, inner call 2C4 selects entry 36 in ROM range 090–0CF. ROM
address 0B4 contains 25, selecting 225. That leaf loads Q=CC at cycle 186.
The outer POP at 2C5 returns to 220 at cycle 189, preserving the prepared
registers. The complete run first reaches 084 at cycle 228 and visits 187
used words. The listing records this as its own `reset_q2_nested_visited`
column, separate from the other selected reset examples.

These lookup addresses and bytes are reconstructed from the hash-verified
Am27S31 dump and checked against executed targets. They remain a candidate
ROM address path, not observed physical bus transfers or sine lookups.

## Why this path does not underflow at 2FF

The calling context is essential:

| Instruction | Transfer | Live depth before → after |
| --- | --- | --- |
| 2FE | Call 21A | 1 → 2 |
| 21F | Call 2BC | 2 → 3 |
| 2C4 | Call 225 | 3 → 4 |
| 227 | Return to 2C5 | 4 → 3 |
| 2C5 | Return to 220 | 3 → 2 |
| 220 | Return to 2FF | 2 → 1 |
| 2FF | Return to 213 | 1 → 0 |

The real four-entry stack is sufficient. No frame is inserted or repaired.
Unlike the failing diagnostic path documented in [LAST-ENTRY.md](LAST-ENTRY.md),
this reset path enters 2FD with an existing caller frame. Reaching the same
return address does not imply the same stack safety.

## Matched index-source comparison

For seed 115, changing only the index source at 2C4 preserves the complete
trace before cycle 185 and the incoming register/stack state:

| Source | Selected entry/target | Q at outer return | Return cycle |
| --- | --- | --- | --- |
| Seeded scenario | 36 / 225 | CC | 189 |
| Current Y | 0 / 2B3 | 00 | 193 |
| Q | 0 / 2B3 | 00 | 193 |
| Previous Y | 0 / 2B3 | 00 | 193 |

All three datapath candidates are zero here: the call computes zero AND Q,
Q is zero, and preceding Y is R5+Q with R5=0. The 2B3 leaf stores D+Q in
R15 and preserves Q, whereas 225 loads Q from D. Thus choosing an index
source changes the routine's data flow even though each alternative returns
cleanly. Clean execution alone does not select the right source.

The comparison artifacts stop immediately after the outer return, with two
legitimate caller frames still present. Later random choices are excluded
from the comparison: using a datapath index consumes one fewer random draw,
so later dispatches would otherwise be confounded by RNG state. The complete
512-cycle scenario witnesses separately demonstrate the balanced continuation.

## Artifacts and reproduction

The [report](results/nested-reset-study/report.json) records all 4,096 runs,
the five nested calling states, their register-writer provenance, source hashes,
trace digests and matched comparisons. Two full scenario traces cover both
observed leaf targets; four additional traces cover the source comparison.
Every observed complete nested call matches the earlier independent arithmetic
prediction, now with real reset-produced RAM and Q.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/nested_reset_study.py
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -p 'test_*.py'
```

The [configuration](nested-reset-study.json) retains the input and dispatch
assumptions. The first witness was found during an exploratory seeded search;
the reported sweep includes the full fixed range, including runs that do not
enter the nested wrapper. There is no new physical-I/O claim or globally
validated dispatch-source assignment.
