# Exceptional call at 1A2: local return-table hypothesis

*Runs under the [shared assumptions](../ASSUMPTIONS.md).*

Treating 1A2 as a computed call into 1E5–1E8 reaches **822 of 1,021 words
(80.51%)** across the same 128 reset-based seeds used by the handler study.
A diagnostic call that merely returns reaches 818 words (80.12%). Thus most
of the coverage gain diagnoses the missing continuation after 1A2, rather
than establishing the particular table target. The local-table association
remains a hypothesis.

## Evidence

Under the common candidate destination field, 85 of 87 BSR words have the
usual no-load destination. The exceptions are 07E and 1A2. 07E is already
modeled as computed, but bit 17.7 makes 1A2 appear direct. Its nominal target
300 ultimately enters paths to 07B/084 instead of returning. The baseline
static graph therefore never reaches the continuation at 1A3, despite the
following calls and arithmetic code. A non-returning call could be intentional;
this observation alone does not prove the address-source bit is wrong.

The same region contains four adjacent POP words at 1E5–1E8, immediately after
an unconditional branch. They have no direct callers and use the same register
fields, with varying arithmetic controls. This is a plausible short dispatch
table. Proximity, the unusual call word, and the missing continuation support
testing an association with 1A2; they do not recover its address/index source.

The experiment compares three scenarios without changing initial PC or RAM:

| Scenario | Static reachability | Dynamic coverage | Stack exceptions |
| --- | --- | --- | --- |
| Previous handler hypothesis | 775 | 770 (75.42%) | None |
| 1A2 calls a returning surrogate at 08A | 837 | 818 (80.12%) | None |
| 1A2 calls the four-entry 1E5 table | 841 | 822 (80.51%) | None |

The surrogate at 08A is explicitly a diagnostic stub, not a proposed physical
target. The local-table scenario adds 52 dynamically visited words and loses
none compared with the handler baseline. Its maximum observed stack depth is
three; the baseline used four. There are still 180 statically unresolved words
under this candidate, and the plan's 90% target is not reached.

## Table arithmetic and limitations

In Q-independent layouts 1, 2 and 4, the entries operate on A=R13 and B=R3,
write R3, and return. Let C be the preceding arithmetic carry, as selected by
the current carry hypothesis. Results modulo 256 are:

| Entry | R3 result |
| --- | --- |
| 1E5 | A − B − 1 + C |
| 1E6 | A + B + C |
| 1E7 | B − A − 1 + C |
| 1E8 | B − A − 1 + C |

These are add/subtract-with-carry operations, not necessarily plain addition
and subtraction. The fixture explicitly tests both incoming carry values.
Layout 3 instead selects (0,B), eliminating dependence on R13 at these words.
No external observation yet selects between those meanings.

The last two entries differ in raw chip-10 bit 7 but have identical modeled
ALU/register effects. That bit may control something outside the modeled
arithmetic. The equivalence is preserved as an unresolved observation, not
hidden or repaired with invented writes. Actual I/O and dispatch encoding
remain unknown.

## Execution and implementation

Explicit entries in `dispatch.tables` now override the probable direct hint
at that call site, just as `branch_tables` already can for branches. The override
changes only target selection: the original condition still controls whether
a call occurs, and a taken call still pushes its real return address. Static
analysis uses the same precedence. No global wiring bit is relabeled.

The two new scenarios each run 128 seeds for 1,000 cycles; the matched baseline
is the saved handler suite, with its seed count and cycle count checked before
reuse. A million-cycle integrated run uses Q-independent layout 2, seed 11,
and external D=55. It finishes cleanly. Full replays of this run and the prior
handler integration reproduce their summaries and transition digests exactly.
The functional/assumption suite passes 42 tests, including conditional call
suppression, the real return to 1A3, graph consistency and carry-sensitive table
arithmetic.

## Reproduce and inspect

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/exception_study.py \
  --integrated-cycles 1000000 --out /tmp/nokia-exception-study
```

Without the optional integration length, only the short suites and analyses
run. [Configuration](../exception-call.json) records hypotheses and fixture inputs.
[Evidence](../results/exception-study/evidence.json),
[scenario comparison](../results/exception-study/summary.json),
[table arithmetic](../results/exception-study/table-arithmetic.json),
[selected graph](../results/exception-study/graph-local_table.json), and
[integration](../results/exception-study/integrated/summary.json) preserve results.

The next unresolved address-source questions remain 26F, 21F and 2C4. The
returning-call control demonstrates why increased coverage alone cannot settle
their target identities.
