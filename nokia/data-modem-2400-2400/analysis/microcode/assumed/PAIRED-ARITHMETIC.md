# Paired arithmetic hypothesis

*Runs under the [shared assumptions](ASSUMPTIONS.md).*

**Caller follow-up:** [CALLER-STATES.md](CALLER-STATES.md) finds reachable
nonzero-Q states that violate the simple rotation formula in variants 1 and 2.
Variant 3 only exercises zero source pairs in the tested profiles.

The chip-10 differences that the previous [register study](REGISTER-FIELDS.md)
could not explain can encode ALU functions and carry inputs. Three retained
layouts implement paired arithmetic in the dispatch tables under explicit
assumptions. This supplies tentative routine meanings, not recovered hardware
wiring. Control-flow coverage remains 55.34% in the branch study; this experiment
does not improve it or meet the overall plan's acceptance criteria.

## What the tables do under this decode

Treat adjacent registers as low/high bytes of 16-bit quantities. With Q zero,
3C5 and 3DA copy two quantities X,Y from registers 10–13 into banks 4–7 and
8–11, respectively. Their four entries produce:

| Entry | First output | Second output |
| --- | --- | --- |
| 0 | X | Y |
| 1 | −Y | X |
| 2 | −X | −Y |
| 3 | Y | −X |

Arithmetic wraps modulo 65536. These are quarter-turn rotations of a pair.
The sign inversion spans both bytes: carry from the low byte feeds the high
byte, including the low-byte-zero case. Q zero is a fixture precondition;
we have not established it at every real call site.

**Counterexample:** 3EF writes into registers 12–15, overlapping the source Y.
Sequential writes change subsequent reads. For X=1234 and Y=5678 (hex), its
four outputs are (1234,1234), (A988,1234), (EDCC,1234), (5678,EDCC).
Thus this table cannot be labeled as another independent rotation under the
same model. Possible missing storage or a different decode remains unresolved.

The first family, 379/392/3AB, combines A=(registers 4–7) with B=(banks 4/8/12).
Under an explicitly virtual grouping of ALU-Y outputs, entries produce:

| Entry | First output | Second output |
| --- | --- | --- |
| 0 | Bx + Ax | By + Ay |
| 1 | By + Ay | Bx − Ax |
| 2 | Bx − Ax | By − Ay |
| 3 | By − Ay | Bx + Ax |

These entries leave register RAM unchanged. In the first bank, A and B alias,
so some results double and others become zero. Output grouping uses chip-10
bits 1,5,6,7 as slot tags; the logged `virtual-phase-output[...]` addresses
are **not identified physical addresses, DAC writes, or output enables**.

## Search and assumptions

[rotation-search.json](rotation-search.json) records the constraints and priors.
Sixteen three-bit source windows with inversions and 2,688 function assignments
leave 480 candidates satisfying the chosen positive/negative arithmetic
identities. Ranking favors arithmetic operations, B use in the first family,
and fewer inversions. These scores are not confidence estimates.

All three retained variants use function bits `10.3,10.2,!10.0` and destination
bits `11.7,11.6,11.5` (LSB first). They differ in source bits. Register fields
remain disjoint from instruction fields. Chip 10 is no longer treated solely
as a D immediate; D is an external zero stub during integration.

Carry is 10.4 unless 11.0 selects the preceding ALU carry. Choosing 11.0 is
unproven: 10.1 also fits the table patterns. Logical-operation carry remains
unknown in the component model; the scenario explicitly supplies zero on an
unknown feedback read and counts those substitutions. The runner preserves
constant-carry scenarios and their original summary/trace format.

The arithmetic identities are search constraints, so reproducing them is a
consistency test, not independent validation. The 3EF overlap is retained as
negative evidence. Neither sine-ROM access, sample timing, controller exchange,
nor physical ADC/DAC connectivity has been identified.

## Verification and reproduction

Each variant passes 312 rotation cases and 468 virtual-output cases covering
zero, byte carries, sign boundaries and seeded random values. Six integrated
runs complete 33 million cycles without stack errors (maximum depth three).
Seed 0 reaches 134 words and logs no virtual writes; seed 4 reaches 177 words
and logs four. These traces still spend nearly all their time in short loops.
Unknown carry feedback occurs 18 times for seed 0 and 14 for seed 4.

The functional/assumption suite passes 32 tests and the board suite passes 18.
Tests include two-byte negation, explicit unknown-carry substitution, mapping
validation, and the overlapping-register counterexample. Full million-cycle
replays check the old constant-carry runner and the new seed-4 trace. Analysis
artifacts regenerate byte for byte; see [verification](results/rotation-study/verification.json).

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/rotation_study.py \
  --out /tmp/nokia-rotation-study
```

Use `--analysis-only` to regenerate mappings, listings, rankings and arithmetic
fixtures without long integrations. `--cycles` reduces integration lengths.

- [Ranking](results/rotation-study/ranking.json)
- [First mapping](results/rotation-study/variant-1.json), [scenario](results/rotation-study/scenario-1.json), and [listing](results/rotation-study/variant-1.csv)
- [Arithmetic examples and counterexample traces](results/rotation-study/arithmetic-1.json)
- [Integration summary](results/rotation-study/summary.json)

Next discriminating evidence should come from callers: whether they establish
Q=0, preserve source pairs for 3EF, and supply a meaningful dispatch index.
Additional clean cycles alone cannot settle those questions.
