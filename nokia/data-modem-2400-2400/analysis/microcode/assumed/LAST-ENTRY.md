# 2DF: a successful reset entry and an input-dependent failure boundary

*Runs under the [shared assumptions](ASSUMPTIONS.md).*

**q3 and q4 now execute 2DF from reset and reach terminal 084 cleanly.**
The same diagnostic gate fails on many other inputs: 1,279 of the 1,536 runs
with the extension stop at an unknown-stack POP at 2FF. Successful entry is
therefore a constrained witness, not validation of a generally safe gate.

This closes the reset-witness gap for the 22 words outside the default graph,
across explicitly different retained mappings and scenarios. It does not
mean that one model executes the whole store correctly, and it does not
complete the broader plan.

## Diagnostic alias-class extension

The new clause, appended to the previous alias scenario, is:

```json
["!10.2", "!10.3", "!10.7", "!11.0"]
```

It makes exactly the identical-word class 0EA, 0FF, 2DB, 2DE, 30A, 334, 352
and 356 newly conditional. The script checks that equality against the actual
PROM rows. The resulting conservative graph reaches all 1,021 used words but
reports 20 possible stack-underflow/overflow sites. It is saved as a separate
diagnostic scenario; default runtime and listing labels are unchanged.

## Matched input sweep, including failures

`last_entry_study.py` compares the previous and extended gates for all six
retained mappings, constant dispatch index 2 and every default D byte. RAM/Q
start at zero. Reads at 117/106 supply D then zero. Each run has a 512-cycle
bound; no stack frame, flag or register value is injected.

| Mapping | Previous gate: terminal | Extended: terminal | Extended: error |
| --- | ---: | ---: | ---: |
| q1 | 256 | 0 | 256 |
| q2 | 256 | 255 | 1 |
| q3 | 256 | 1 | 255 |
| q4 | 256 | 1 | 255 |
| fitted_original | 256 | 0 | 256 |
| fitted_swapped | 256 | 0 | 256 |

All 3,072 runs either reach 084 or stop on an error by the bound; none ends
in a nonterminal state at 512 cycles. Every error stops at 2FF with `unknown stack at PC 2ff`. The report
retains those stops, stack counters and traces instead of repairing the stack
or discarding failed cases.

The only clean runs that visit 2DF are q3/D=FF and q4/D=FF. They first execute
084 at cycles 283 and 282 respectively. q2's extended D=00 case fails; its
other 255 cases terminate without visiting 2DF.

## Why the FF cases work

Both successful traces enter 2DF with R0=0, Q=0 and an empty live stack.
The relaxed branch at 2DB falls through to 2DC; zero from 2DD then permits
2DE to fall through to 2DF. Under q3, 2DF exposes R4−R0 (FE in this witness);
under q4, it exposes R4 (00). Neither operation changes RAM or Q.

The following instructions form a masked-input test:

1. 2E0 loads its external byte into Q.
2. 2E1 ANDs its external byte with Q.
3. 2E2 exposes an addition without storing it. Fixed-false select 1 at the
   skip instruction 2E3 preserves the following path; 2E3's ALU produces zero.
4. Gated 2E4 therefore falls through. Its own ALU computes R0−Q−1, using
   the zero carry produced by 2E3.
5. Gated 2E5 tests that preceding result: zero continues at 2E6, nonzero
   branches to 2FD.

Writing the two read bytes as d0 and d1, the continuation condition is

`d0 & d1 == (R0 − 1) mod 256`.

At the observed reset entry, R0=0. The condition therefore requires both
bytes to be FF. q3/q4 preserve that FF mask, pass through 2E6–2EB, then enter
160 and use normal subsequent calls and returns before reaching 084.

For the failing q3/q4 byte inputs, the condition is false. Execution branches
to 2FD, calls the existing 21A dispatch routine, and eventually executes the
POP at 2FF without a caller frame. The observed failures are specific to this
reset/dispatch setup; the local predicate alone does not prove that every
possible path through 2FD must fail.

The shared q2 decode clears Q at 2E1 instead of masking the external byte,
so the same successful-input argument cannot simply be transferred to q2.
A real input protocol might supply the required bytes, but no such protocol
or physical channel has been identified. This is an explicit diagnostic
input condition, not a hardware claim.

## Exhaustive local checks

`masked_entry_study.py` stops before subsequent call/return behavior and checks
2DF–2E5 directly with the actual sequencer/datapath models. For each of q3 and
q4 it covers:

| Domain | Cases | Continue at 2E6 | Branch to 2FD |
| --- | ---: | ---: | ---: |
| Every R0/masked-Q pair | 65,536 | 256 | 65,280 |
| Every d0/d1 pair with R0=0 | 65,536 | 1 | 65,535 |

That is 262,144 cases across both mappings. Every case checks the instruction
path, first ALU result at 2DF, comparison result at 2E4, unchanged full RAM,
Q equal to the input AND, and balanced stack activity. The input-pair domain
shows directly that only (FF,FF) satisfies the zero-R0 entry condition.
Local cases are not all claimed reachable from reset.

## Reproduce

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/last_entry_study.py
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/masked_entry_study.py
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/program_reading.py
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -p 'test_*.py'
```

The [runtime report](results/last-entry-study/report.json) records all matched
outcomes, explicit failures, graph exceptions, source hashes and 24 complete
00/FF traces. The [local report](results/masked-entry-study/report.json)
records the exhaustive domains and representative cases. A clean witness is
not used to hide the failure boundary or promote this diagnostic gate.
