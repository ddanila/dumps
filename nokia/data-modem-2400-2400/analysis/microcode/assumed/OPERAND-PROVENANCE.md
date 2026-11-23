# Where the paired-arithmetic operands come from

Expanding the ROM-feedback experiment from 16 to 128 seeds does not produce
nonzero inputs at the three paired-transform call sites. Tracking the last
writer of each source register explains the observed zeros more precisely:
in these traces, calls receive either initialized zero bytes or zeros written
by earlier entries in the same transform tables.

This is a statement about the saved reset-started scenarios. It does not prove
that hardware input is absent, that the routines never receive nonzero values,
or that the register decode is correct.

A [stack-aware follow-up](OPERAND-PATHS.md) now shows that the missing writer
connections hold across the entire declared graph, beyond the sampled runs.

## Experiment

[operand-search.json](operand-search.json) declares four Q-independent layouts,
two fixed ROM banks, seeds 0–127, and 1,000 cycles per run. Read policies and
control flow are inherited from [the feedback experiment](ALU-FEEDBACK.md).
No entry point or initial register value is injected. The complete bounded
prefix of each run is used to reconstruct registers before the table entry.

For each instruction, destination codes 2–7 count as a RAM write even when
the stored byte does not change. The runner's ordinary delta trace omits
unchanged register values, so relying on those deltas alone would falsely
attribute some operands to initialization. At each computed call, the report
records registers 10–13 and their last writers after the call instruction's
own datapath operation, before the target executes.

Each profile observes the following calls:

| Call site | Observations | Nonzero source pairs |
| --- | --- | --- |
| 3C2 | 14 | 0 |
| 3D7 | 8 | 0 |
| 3EC | 36 | 0 |

All 1,024 runs finish cleanly. Every profile has 58 observations, including 18
where all four source bytes still come from the scenario's initial state.
The other 40 have at least one explicit source-register write before entry.
Identical call counts across profiles are not independent hardware evidence:
conditions and dispatch indices are still scenario-driven.

## Last writers and their implications

For variant 2, lower bank, the 58 calls have these last writers. Addresses
are hexadecimal; counts apply separately to each register in the pair.

| Registers | Last writer PCs and observation counts |
| --- | --- |
| R10 / R11 | initial: 44; 3E0 / 3E1: 7; 3DC / 3DD: 1; 3E8 / 3E9: 3; 3E4 / 3E5: 3 |
| R12 / R13 | initial: 18; 3F3 / 3F4: 11; 3FB / 3FC: 9; 3EF / 3F0: 12; 3F7 / 3F8: 8 |

These instruction writers belong to the paired-transform tables. Under this
decode they copy or negate bytes from the same source-register group; the
saved values are zero. The observations thus expose repeated transforms of
zero state, rather than a demonstrated input-loading path into the transforms.

All 43 statically decoded instructions capable of writing R10–R13 are visited
somewhere in every profile. Consequently, the zero inputs are not explained
merely by failing to visit every potential writer. Aggregate coverage does
not establish that a writer ran before the relevant call on the same path.
The per-call records preserve that distinction. Examples of other writers
include 094–097 copying R0, 38C–38D copying R6–R7, and 3A3–3A4 copying R4–R5
under variant 2. None appears as a last writer in the table above.

The next discriminating question is whether an input-producing path can
connect to these calls under a coherent condition/dispatch scenario, or
whether the operand/register decode must change. Adding more cycles to the
same terminal loops cannot answer it.

## Reproduce and verify

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/operand_study.py \
  --out /tmp/nokia-operand-study
```

[Summary](results/operand-study/summary.json) and
[variant-2 lower-bank report](results/operand-study/variant-2-bank-000.json)
include run digests, per-call writer records, and the static writer listing
with visitation flags. The functional/assumption suite passes 48 tests,
including a fixture that distinguishes unchanged writes from initial state,
checks call-instruction writes, preserves earlier observations, and rejects
noncontiguous trace prefixes. One observed-call seed per profile was replayed
independently: all eight run digests and per-call records matched. Report
invariants were checked across all eight profiles. The full plan remains incomplete.
