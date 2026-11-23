# Control-flow separation of source writers and transforms

The zero-input result is not just a consequence of testing too few random
seeds. Exhaustive stack-aware exploration of the current ROM-backed control
flow finds no path from any of the 27 source-register writers outside the
transform tables to calls 3C2, 3D7 or 3EC. Only 16 writers within those tables
can precede the calls. This holds for all four current datapath layouts.

The conclusion is conditional on the saved branch/dispatch edges and register
decode. It does not establish what the physical modem does, and does not prove
that these calls are intended to process nonzero samples. Initialization is
another possible role that must be tested rather than assumed away.

The [expanded source/register-role search](PREPARATION-DECODE.md) tests the
preparation-routine question below against the existing arithmetic fixtures.

## Method and scope

`graph(..., include_states=True)` optionally exposes edges between complete
`(PC, return-stack)` states. The default output remains unchanged. Reverse
reachability starts at all reset-reachable contexts of the three call sites.
Keeping the stack prevents a return from one caller being incorrectly joined
to another caller's continuation.

The graph explores 1,307 states without truncation or exceptions. Of those,
141 can precede one of the calls. All 43 decoded instructions writing R10–R13
are reset-reachable, but only these can also reach a later transform call:

- R10/R11: 3DC–3DD, 3E0–3E1, 3E4–3E5, 3E8–3E9.
- R12/R13: 3EF–3F0, 3F3–3F4, 3F7–3F8, 3FB–3FC.

These are exactly the writers seen in the [128-seed provenance report](OPERAND-PROVENANCE.md).
The static analysis considers both outcomes of conditional branches and all
declared table targets. Thus further random choices among those same edges
cannot make an excluded writer feed a call. This is a control-flow exclusion,
not an exhaustive proof of all possible numerical states.

The analysis refuses to draw this conclusion if graph exploration reports
any exception, including its state-budget limit. New external entries, missing
branch targets, an altered unconditional-condition rule, or another register
decode require rerunning the analysis.

## A concrete decode question: preparation routine 341–344

There are two relevant caller sequences: 133 calls 341 before the transform
calls at 13B–13D; 18B calls 341 immediately before 18C calls 3EA. The latter
routine contains computed call 3EC. This makes 341–344 a useful place to test
why the current model does not prepare transform operands.

All four current layouts decode that routine identically:

| PC | Raw PROM bytes (10,11,17,18) | A | B | Source | Destination |
| --- | --- | --- | --- | --- | --- |
| 341 | B5 CA 04 3C | 10 | 0 | 0,Q | RAM[B] |
| 342 | B5 DB 04 3C | 11 | 0 | 0,Q | RAM[B] |
| 343 | 75 C6 04 3C | 12 | 0 | 0,Q | RAM[B] |
| 344 | 75 D7 06 3C | 13 | 0 | 0,Q | RAM[B] |

The function is `~R + S + carry`, where R is zero and S is Q. The decoded
A field counts through precisely the four transform-source registers, yet
this operand source ignores A and every instruction writes R0. This is a
specific tension to investigate in the source/register decode or possible
external transfer interpretation. It is not sufficient evidence to swap A/B,
invent a load into R10–R13, or label the routine a proven input loader.

The earlier quarter-turn interpretation was a search constraint, not an
independently recovered algorithm. Any proposed decode change must be tested
against this caller context as well as against those arithmetic fixtures.

## Reproduce and verify

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/operand_paths.py \
  --out /tmp/nokia-operand-paths
```

[Summary](results/operand-paths/summary.json) and
[variant-2 report](results/operand-paths/variant-2.json) preserve the ancestor
states and each writer's connectivity. The functional/assumption suite passes
49 tests. The new test uses two calls to the same routine with different
returns, verifies that reverse traversal preserves the caller distinction,
and checks that optional context output leaves the original graph unchanged.
The full plan remains incomplete.
