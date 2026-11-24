# Second register field and a datapath limitation

*Runs under the [shared assumptions](ASSUMPTIONS.md).*

The PROM tables support a second four-bit register-number field:
**LSB-first `11.4, 11.3, 11.2, 11.1`**. This is a unique match within the
specified contiguous-field search. The observed counting pattern is recovered
from data; assigning this field to Am2901 A rather than B remains a hypothesis.

The new instruction candidates are more constrained, but they still do not
explain why the first three dispatch-table families have four different
entries. That negative result is more informative than another clean run.

## Register evidence

The first three 16-word tables use the same four positions in each entry.
Requiring the second field to count 4,5,6,7 across these positions gives one
exact match over 48 words, out of 74 distinct contiguous windows × 16 polarity
masks = **1,184 candidates**. The known register field is excluded from the
search, so it cannot trivially match itself. Chip order and both bit directions
are searched. The target pattern and search boundaries are explicit hypotheses
in [register-search.json](register-search.json).

The remaining three tables and the one-word selector table are held out from
that score:

| Table base | New field | Existing field |
| --- | --- | --- |
| 379 | 4,5,6,7 in each entry | 4,5,6,7 |
| 392 | 4,5,6,7 in each entry | 8,9,10,11 |
| 3AB | 4,5,6,7 in each entry | 12,13,14,15 |
| 3C5 | 10,11,12,13 or 12,13,10,11 | 4,5,6,7 |
| 3DA | 10,11,12,13 or 12,13,10,11 | 8,9,10,11 |
| 3EF | 10,11,12,13 or 12,13,10,11 | 12,13,14,15 |
| 08A–099 | Always 0 | Counts 0–15 |

This supports a structure involving paired registers and three four-register
banks. It does not establish the arithmetic, byte order, register widths, or
whether either field also drives external circuitry.

## Constrained instruction search

The new search fixes the two candidate register fields and excludes their bits
from the nine instruction bits. The historical layouts overlapped the newly
identified field, or treated parts of chip 10 as a second register field. Those
layouts remain saved for reproducibility but are not promoted as recovered
wiring.

Instruction candidates use contiguous windows of residual bits, both physical
bit directions, permutations of the three instruction groups, all 512 polarity
masks, and both A/B roles. Conditions may reuse 17.4/17.5 as datapath controls;
this is explicit in the configuration. The search still assumes chip 10 is a
reversed immediate and therefore does not test chip-10 instruction layouts.

The ranking uses declared priors: common no-load/RAM-load destinations, few
shifts overall, no-load at eight plain computed-call words, a shift at 1E9,
arithmetic-operation frequency, and a small penalty for inversions. These are
not independent measurements or confidence probabilities. In particular,
source-code polarity has no semantic anchor in this score.

The top candidates put destination controls at `11.7,11.6,11.5`, producing
88.15% common destinations and 4.51% shifts across used words. The top two tie
and swap A/B; the third changes an ALU-function inversion. All three complete
10 million integrated cycles with the branch-table scenario, maximum stack
depth three, and 134 visited words in seed 0. Register-change counts are 115,
127, and 115. These runs do not improve control-flow coverage or identify I/O.

## Why these layouts are still incomplete

At 379, 392 and 3AB, the four alternative entries differ in chip 10. Under all
three candidate layouts:

1. Each corresponding step has identical decoded instruction and register
   inputs across the four alternatives.
2. The decoded Am2901 source does not use D.
3. Therefore the differing chip-10 immediate cannot affect any modeled register
   or ALU output, for any initial register state and common carry/shift inputs.

All four alternatives have identical modeled datapath effects. In the other
three families, entries 0/2 are equivalent and entries 1/3 are equivalent.
This is a structural result, also checked with nonzero register/Q fixtures;
it does not depend on a particular reset state. It excludes unmodeled external
I/O, so it is not a claim that the real hardware behaves identically.

The next investigation must explain the changing chip-10 values: they may be
external addresses/control, instruction bits, or data selected through a
missing path. The current immediate-only interpretation and empty baseline
I/O rules cannot account for the differences. Adding arbitrary writes solely
to make the traces different would not resolve this evidence gap.

## Reproduce and inspect

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/register_study.py \
  --out /tmp/nokia-register-study
```

Use `--analysis-only` to regenerate the search and semantic comparison without
long runs. The default performs three 10-million-cycle integrations. These
results supplement rather than overwrite either historical suite.

- [Recovery, search bounds, and held-out patterns](results/register-study/register-recovery.json)
- [Instruction ranking and explicit priors](results/register-study/ranking.json)
- [Equivalent-entry analysis](results/register-study/table-semantics.json)
- [Integration summary](results/register-study/summary.json)
- [First candidate mapping](results/register-study/variant-1.json) and
  [decoded listing](results/register-study/variant-1.csv)

The functional/assumption suite now passes 29 tests, including uniqueness of
the register-pattern match, disjoint instruction/register fields, and the
negative table-equivalence test. Overall PLAN.md acceptance remains incomplete.
