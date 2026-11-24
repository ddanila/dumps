# Consistent flag policies for the two numerical-use witnesses

*Runs under the [shared assumptions](ASSUMPTIONS.md).*

Both [downstream-use witnesses](FIRST-USE.md) can be replayed by the main
integrated runner using one preceding-instruction flag source and polarity
per condition selector. No instruction-specific condition override is needed
for these local paths. The zero and marked-input runs reproduce their earlier
PC transitions, RAM, Q and ALU-Y values.

This is consistency with prescribed fixtures, not recovered condition wiring.
Many fits are possible, and several selected flags remain constant over the
observations. A successful fit does not show that the board uses that source
or that other program paths remain valid under the same policy.

A [broader execution follow-up](CONDITION-EXTENSION.md) now tests these
policies beyond the fitted paths. Clean runs do not yet reach preparation
from reset; some broader branches also consume unknown flags.

## Fit method

The study re-executes each saved trace with the component datapath and carry
policy. It checks every carry input and resulting RAM/Q/Y against the saved
trace, then records current and preceding zero, sign, carry and overflow flags
at instructions that actually consult TEST. Unconditional transfers are
excluded from fitting; INC, POP and PLP do not constrain TEST.

For each selector, one source and polarity must match every observation in
both the zero-input and marked-input trace. Unknown flags do not count as a
verified fit. The report separates known mismatches from unknown values.
Constants are reported as alternative external-input hypotheses, not identified
hardware lines. Unobserved selectors remain unconstrained.

Select 3 has no fully known current-flag fit in either witness. Logical carry
and overflow are partly unimplemented in the component model, so this does
not rule out the physical current carry/overflow pins. Preceding flags have
multiple verified fits. In particular, original roles allow inverted preceding
carry or overflow; swapped roles additionally allow preceding zero or inverted
sign. This is not sufficient evidence to choose a physical latch phase.

## Policies replayed through the main runner

The following explicit hypothesis choices are saved in
[condition-fit.json](condition-fit.json). Every source below is sampled from
the preceding executed instruction.

| Selector | Original-role candidate 31 | Swapped-role candidate 31 |
| --- | --- | --- |
| 0, when conditional | NOT zero | NOT zero |
| 2 | carry | unconstrained, fixture constant 0 |
| 3 | NOT carry | zero |
| 6 | unconstrained, fixture constant 0 | zero |
| 7 | zero | NOT zero |

Unused selectors use constant zero. The existing unconditional select-zero
BSR/BRT rule is preserved. Computed dispatch uses the same fixed entry as each
witness (0 for original, 1 for swapped). Initial state, preparation input bytes,
carry fallback and other stubs remain explicit scenario inputs.

The integrated original-role runs complete 57 cycles and stop at 19C. The
swapped runs complete 62 cycles and stop at 1A2. All four are clean and match
the corresponding local trace at every instruction's PC, next PC, RAM, Q,
ALU Y and external D value. TEST values on instructions that ignore TEST need
not match, because those values have no sequencer effect.

The original marked run still carries Q=87 into R4. The swapped marked run
still computes Y=55 at 1A1 instead of FF in its zero-input counterpart. These
are local integrated demonstrations under the saved policies, not reset boots
or additions to coverage.

## PC-keyed external input fixtures

The runner adds `io.read.mode: pc_table` to supply these reproducible inputs.
`pc_values` maps canonical decimal instruction-PC strings to bytes. Unlisted
instructions receive `io.read.value`. The policy requires explicit status and
evidence. Values and PC bounds are validated.

These keys are instruction PCs, **not physical memory addresses**. Each trace
records `external_read` with the value, source `scenario_pc`, assumption status
and whether the ALU selects D. Selecting D does not guarantee mathematical
dependence on it. This fixture capability does not infer a memory bus or any
hardware read enable. Existing read modes and their output formats are
unchanged.

## Verification and reproduction

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/condition_fit.py \
  --out /tmp/nokia-condition-fit
```

[Fit summary](results/condition-fit/summary.json),
[original marked replay](results/condition-fit/original-marked/summary.json),
and [swapped marked replay](results/condition-fit/swapped-marked/summary.json)
retain the evidence. Each replay directory includes its exact mapping,
scenario and complete short trace. All 21 files reproduce byte for byte.
The functional/assumption suite passes 55 tests, including unknown-flag
handling, polarity fitting, PC-keyed reads/defaults and provenance validation.
The historical million-cycle ROM-feedback run also replays unchanged.

The next meaningful test is broader execution under these fitted policies,
including inputs that vary the fitted flags. Neither the mapping nor the
condition assignments should be promoted from short, selected traces. The
full plan remains incomplete.
