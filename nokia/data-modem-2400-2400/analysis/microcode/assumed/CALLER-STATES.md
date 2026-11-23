# Caller states challenge the simple rotation interpretation

The [paired-arithmetic experiment](PAIRED-ARITHMETIC.md) fits quarter-turn
identities with Q=0. Reset-path traces show that this precondition depends on
the external input stub. It is not established as a program invariant.

The reproducible caller study runs all three saved mappings with seeds 0–15,
starting at reset, for 1,000 cycles each. Four explicit constant external-read
profiles (00, 01, 55, FF hex) give 192 runs and 192,000 cycles. All runs finish
cleanly. No entry PCs or register values are injected. Conditions and table
indices remain scenario-driven; these profiles test sensitivity, not actual
modem input. Long runs were unnecessary: the relevant calls occur in the
bounded prefixes already observed in the branch study.

## Findings

Each variant/profile observes three calls at 3C2, four at 3D7, and six at 3EC.
The first two call tables 3C5/3DA; the third calls the overlapping table 3EF.

| Mapping | External D | Q at the 13 calls | Sources R10–R13 | Simple rotation at 3C5/3DA |
| --- | --- | --- | --- | --- |
| 1 or 2 | 00 | Always zero | Always zero | 7/7 match, but all-zero inputs |
| 1 or 2 | 01, 55, FF | Always nonzero | Often nonzero; always nonzero at 3C2/3D7 | 0/7 match per profile |
| 3 | Any tested value | Always zero | Always zero | 7/7 match, but all-zero inputs |

For example, variant 1 with D=01, seed 11, reaches 3D7 at cycle 67 with
Q=01, X=0000, Y=0101. Entry 1 would produce (FEFF,0000) as a quarter turn.
The decoded instructions instead produce (0000,0101), because Q contributes
to the arithmetic. This is a reachable-state counterexample, in addition to
the earlier independent 3EF register-overlap counterexample.

Thus neither the two nonzero-input failures nor variant 3's zero results
identify the correct wiring. The tables may perform more general arithmetic
involving Q, callers may need a different decode, or external-input selection
may be missing. We do not promote variant 3 merely because it passes a test
with zero operands.

## Dispatch observations

At the common computed-call word, the mappings disagree about the datapath
operation. With D=00 all observed calls at 081 and the six arithmetic-table
sites have current Y=0. Using its low bits as the dispatch index would always
select entry zero there. Scenario-driven execution exercises other entries.
This shows why switching to current Y under the zero-input stub would discard
coverage without identifying an address source.

The reports also record Q and the preceding instruction's Y as candidate
indices. Some become nonzero when D changes, but no observed physical address
selects among them. These are counterfactual indices on the existing paths,
not executions with those alternative dispatch policies. Calls at 21F and
2C4 remain unobserved and their table assignments remain explicit stubs.

## Reproduce and inspect

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/caller_study.py \
  --out /tmp/nokia-caller-study
```

[Configuration](caller-search.json) records input values, seeds, cycle limit
and limitations. [Summary](results/caller-study/summary.json) separates every
variant and input profile. [Variant 1](results/caller-study/variant-1.json)
contains per-call RAM/Q snapshots, reconstructed before/after states, candidate
indices, expected/actual arithmetic outputs, and decoded caller instructions.
The trace reconstruction test checks timing and rejects incomplete prefixes.
The functional/assumption suite passes 34 tests.

The next useful constraint is how Q and D are selected during loop setup and
arithmetic, rather than adding execution cycles or accepting the zero-input
rotation label. Coverage and physical I/O identification remain unresolved.
