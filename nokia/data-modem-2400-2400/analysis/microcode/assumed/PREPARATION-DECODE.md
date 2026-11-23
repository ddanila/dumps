# Testing the preparation routine against the arithmetic decode

A broader source-field search does not resolve the operand-loading question.
It finds more layouts compatible with the old arithmetic fixtures, including
four that select external D at 341–344. With the existing register fields,
all still write R0. Swapping A/B makes that routine write R10–R13, but none
of the swapped candidates preserves the existing forward-transform fixtures.

This exposes a tradeoff between hypotheses, not proof of a hardware fault or
of the correct decode. In particular, the forward quarter-turn identities
were imposed during search. Their failure cannot by itself reject a different
algorithm with reversed register roles.

A [caller-chain sensitivity experiment](CALLER-CHAIN.md) now tests whether
preparation-byte effects survive the subsequent calls without imposing an
expected arithmetic formula.

## Search scope

[preparation-search.json](preparation-search.json) permits every one of the 32
PROM bits as each of the three source controls, with independent inversion
and distinct physical bits. This evaluates 32 × 31 × 30 × 8 = 238,080 source
assignments. Overlap with command, function, destination or register fields
is allowed and visible in each saved mapping.

The four source-code constraints from the earlier independent-source search
remain fixed: 379→1, 3C5→4, 1E9→2 and 1EA→0. They leave 36 assignments. Each
is tested with both original and swapped A/B roles, giving 72 profiles. The
function bits, destination bits, carry policy, register-number expressions,
virtual output grouping and byte order are otherwise unchanged.

Each profile runs the existing 600 arithmetic checks (240 transform and 360
virtual-output cases) and the all-256-Q loop probe. Sixteen original-role
profiles pass both sets. No swapped profile does. This is a bounded search;
it does not cover arbitrary function/destination rewiring, register muxes,
other arithmetic identities or unknown external transfers.

## What the surviving source fields do at 341–344

The first source bit remains 17.5 in every surviving layout. The possibilities
at the preparation routine are:

| I1 choices | I2 | Operand pair at 341–344 | Surviving layouts |
| --- | --- | --- | --- |
| !11.7, 11.5, 17.0, 18.7 | 11.6 | 0,A | 4 |
| !11.7, 11.5, 17.0, 18.7 | 18.6 | A,Q | 4 |
| !17.3, 18.2, 18.3, 18.4 | 11.6 | D,Q | 4 |
| !17.3, 18.2, 18.3, 18.4 | 18.6 | 0,Q | 4 |

The last row contains the previous four layouts. Some new assignments share
bits with the destination or sequencer fields. Such overlap is an explicit
hypothesis, not a reason to silently discard or promote a candidate.

The D,Q candidates replace source bit I2=18.6 with I2=11.6. In the marked-value
local probe, Q=55 and external D bytes are 12,34,56,78 (hex). Candidate
`preparation-source-07` produces 43,21,FF,DC, writing R0 four times. It leaves
R10–R13 unchanged. With A/B swapped, it produces the same bytes but stores
them in R10,R11,R12,R13 respectively.

The swapped version fails 480 of the existing arithmetic checks. Its first
counterexample is the zero-input identity entry at 3C5: expected output banks
contain (0000,0000), but remain at the fixture's (A5A5,A5A5). The register-role
swap changes which registers the routine writes, so that interpretation of
its inputs and outputs no longer holds.

This local fixture deliberately supplies marked register and input values.
It is not a reset execution, contributes no coverage, and does not establish
that those bytes occur on a physical bus.

## Consequence for reading the program

The [control-flow result](OPERAND-PATHS.md) already excludes all non-table
source writers from the transform-call paths under the current edges. Merely
broadening source controls leaves those register destinations and edges
unchanged. It therefore does not turn 341 into a loader of R10–R13 under the
original register roles.

Further work must test the preparation and table routines together without
assuming the forward-transform interpretation is correct. Missing external
transfers and alternate register/function/destination layouts also remain
possible. None of the 16 survivors is selected as recovered wiring; the older
integrated experiments remain preserved under their original mappings.

## Reproduce and verify

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/preparation_study.py \
  --out /tmp/nokia-preparation-study
```

[Summary and counterexamples](results/preparation-study/summary.json) preserve
all 72 profiles and their local traces. Sixteen named mappings are saved,
including [the D,Q example](results/preparation-study/preparation-source-07.json).
All 17 output artifacts regenerate byte for byte. The functional/assumption
suite passes 50 tests, including a test of the external-D candidate, unchanged
R10–R13 with original roles, changed destinations with swapped roles, and the
resulting arithmetic conflict. The full plan remains incomplete.
