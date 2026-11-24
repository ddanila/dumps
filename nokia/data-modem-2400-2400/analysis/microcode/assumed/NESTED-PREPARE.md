# Shifted-Q preparation and nested ROM dispatch

Under q2, the previously structural-only wrapper at 2BC–2C5 prepares three
registers while preserving Q, then calls a ROM-selected leaf. The leaf can
replace Q with an external input, preserve it while exposing arithmetic
results, or store an input sum in R15. This provides a local arithmetic
interpretation of the [nested-call structure](ROM-TAIL.md).

The experiment starts at the actual call instruction 21F with explicit RAM/Q
fixtures. It executes both real calls and returns, stopping when the outer
call returns to 220. It does **not** establish an integrated reset path to this
routine or identify a physical peripheral. A subsequent
[reset sweep](NESTED-RESET.md) reaches this wrapper in five clean runs, all
with Q=R5=0 on entry; those witnesses complement the nonzero local fixtures.

## Prefix state and transient results

Let `q` be Q on entry, and `D_pc` the input supplied at an instruction. Under
zero-fill shifts and the mapped/previous-carry policy, the state immediately
before call 2C4 is:

| State | Value |
| --- | --- |
| Q | `q`, unchanged |
| R0 | `q >> 1` |
| R2 | `(D_2C2 + q) mod 256` |
| R4 | `((D_2C0 + q) mod 256) >> 1` |
| Other registers | Unchanged |
| Previous Y | `(R5 + q) mod 256`, from 2C3 |

These are byte operations: R4 discards the addition's overflow *before*
shifting. For q=FF and D_2C0=01 it becomes 00, not 80. Q itself is never
shifted by this prefix. The two writes at 2BE and 2BF both put `q >> 1` in R0.
The earlier shifted sum written to R2 at 2BD is overwritten at 2C2.

Several instructions expose additional results without retaining them in RAM.
2BC produces FF from `R4−R4−1`. At 2C1, Y is
`D_2C1−R9−1+carry_2C0`, modulo 256. 2C3 exposes `R5+q`; the following call
computes zero AND Q, making its own Y zero. A transient result may have an
external consumer, so an overwritten internal value is not proof that an
instruction is useless.

## Dispatch sources and real ROM bytes

The outer call uses scenario index 81 in the hypothesized ROM range 080–0D1.
Byte D1=BC plus bank 200 selects 2BC. The inner call retains the scoped range
090–0CF from the earlier stack analysis. Both target lists are checked against
the hash-verified 512-byte Am27S31 dump, and every saved executed lookup is
reconstructed from its ROM address and byte.

| Source at 2C4 | Index before reduction modulo 64 | Observed targets |
| --- | --- | --- |
| Scenario | 81 | 22B |
| Current Y | 0 | 2B3 |
| Q | `q` | All seven |
| Previous Y | `(R5+q) mod 256` | All seven |

The seven targets are 224, 225, 229, 22B, 22C, 22D and 2B3. Q and preceding
Y give the same aggregate target counts in this sweep but can select different
leaves for an individual fixture. Coverage therefore does not distinguish
them. The preparation of `R5+q` immediately before the call makes preceding Y
worth retaining as an explicit candidate, without proving the index wiring.

## What the leaves do in this calling context

| Entry | Effect through return to 2C5 |
| --- | --- |
| 224 | Expose R15, then enter 225 |
| 225 | Load Q from external D; expose `R0 AND R3` and Q; return at 227 |
| 229 | Expose Q, then Q−1; return at 22A |
| 22B, 22C | Expose Q and return |
| 22D | Expose Q−1 three times; return at 22F |
| 2B3 | Store D+q in R15 twice; expose differences; branch to 227 and return |

The nested leaf inputs use one constant byte D per fixture. Thus the two
R15 stores in the 2B3 case retain `(D+q) mod 256`; differing input bytes at
2B3 and 2B4 are outside this sweep. The path through 2B7 computes `q−R0`.
Because this caller prepared `R0=q>>1` and the leaf preserves Q, its carry is
always set. BRT at 2B8 therefore takes 227, bypassing 2B9–2BB. This is a
caller-dependent result, not a global dead-code claim for those three words.

At the outer POP 2C5, q2 exposes the current `Q−1` without storing it. All
leaves preserve the prefix's R0/R2/R4, and only the 2B3 leaf additionally
changes R15. Entries 224/225 replace Q; all other entries preserve it.

## Validation scope

For each of four sources, the study checks all 65,536 `(q,D)` pairs with:

- R5=`D XOR 5A`, R4=`D XOR A5`, R9=`255−D`, and nonzero fixtures elsewhere;
- D_2BD=`q XOR D`, D_2C0=D, and D_2C2=`(73*D+q) mod 256`;
- default D at the other instructions.

For each fixed q, the odd multiplier 73 makes D_2C2 cover every byte, and the
XOR makes R5 cover every byte. Thus the tested pairs exhaust q/D_2C0,
q/D_2C2 and q/R5 individually; they do not exhaust all independent input
combinations or all initial RAM states at once.

All **262,144 local calls** match the independent prefix/final-state formulas
and return to 220 in 12–18 instructions, with maximum stack depth two and
final depth zero. No stack frames are injected or repaired. Each Q/previous-Y
sweep selects 224 in 4,096 cases, 225 in 53,248, 2B3 in 4,096, and each other
leaf in 1,024. Scenario indexing selects 22B in all cases; current-Y indexing
selects 2B3 in all cases.

Sixteen complete integrated witnesses cover every source/target combination
with nonzero initial Q. Their instruction addresses, next addresses, ALU
results and tests match the local model step for step. The report retains
source hashes, an exhaustive execution digest, prefix/final states, and the
reconstructed ROM lookups. The fixtures and scoped table range remain
hypotheses. Nothing here identifies a sine lookup, DAC write, sample rate or
controller exchange.

## Reproduce

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/nested_prepare_study.py
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -p 'test_*.py'
```

[Configuration](nested-prepare-study.json), [script](nested_prepare_study.py),
and [report](results/nested-prepare-study/report.json) preserve the experiment.
