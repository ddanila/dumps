# Plan acceptance audit

The [plan](../PLAN.md) is **not yet complete**. Its execution requirements now
have a consolidated check against the current executor. Program interpretation
still has concrete gaps, including 14 direct-call entries with no annotation.
Physical fidelity is not an additional acceptance gate: the plan explicitly
allows labelled assumptions and makes hardware checks optional.

[Configuration](plan-validation.json), [verification runner](plan_validation.py),
and [current report](results/plan-validation/report.json) preserve the evidence
and keep execution acceptance separate from full-plan completion.

## Current execution evidence

The runner reproduces all 11 original field-analysis artifacts byte for byte,
including the address-window search, condition table, subroutine walk, layout
ranking and listings. It also regenerates the annotated listing and catalog;
that process replays the five reset witnesses explaining the default graph's
22 gaps. All six named mappings decode 1,024 instructions into legal datapath
fields and carry provenance for every named field. Legal decoding alone does
not prove physical wiring or algorithmic plausibility.

The current 128-seed, 1,000-cycle sequencer sweep reproduces every saved digest
and stack result. It visits 941/1,021 used words (92.16%). The following three
long runs each complete one million instructions with no model errors or unused
word executions. Each is then replayed for another million instructions with
an identical complete summary and transition digest.

| Scenario | Mode | Distinct words | Maximum stack depth | End behavior |
| --- | --- | --- | --- | --- |
| Combined local-case tables, seed 0 | Sequencer | 134 | 3 | Terminal 084 |
| Real q2 nested reset, seed 115 | Integrated | 187 | 4 | Terminal 084 |
| q3 ROM/carry loop, reply F9 | Integrated | 78 | 3 | Continues through 36C–36E |

The q3 run performs 333,309 ROM reads selected as ALU operands and 999,941
register changes. It exercises ongoing data/address feedback rather than only
the terminal branch. The q2 and q3 runs preserve the first 256 instructions of
their earlier full witnesses exactly. Captured writes, scenarios, bounded
traces and full-run counters are saved with each result.

The 92.16% figure comes from the **separate short sequencer sweep**. It is not
the coverage of either integrated run, nor a union of different datapath
interpretations presented as one machine. Three million primary instructions
plus three million replay instructions establish this current long-run check.

The original [suite report](results/suite.json) remains unchanged. Its 61 million
primary instructions were clean, but its coverage gate failed at 28.80%.
Later table hypotheses supplied the higher coverage. The new report records
both outcomes rather than relabelling the historical suite as accepted.

## Requirement-by-requirement result

| Plan requirement | Current evidence | Audit result |
| --- | --- | --- |
| Explicit mapping/scenario assumptions and provenance | Named-field validation; unchanged saved scenarios; provenance on ROM/DAC/dispatch policies | Implemented for the audited models and scenarios |
| Unknown inputs become logged parameters | `execute.py` read policies, flag fallback accounting, external-read trace records and captured writes | Implemented; stubs remain labelled |
| Raw dumps and photographs untouched | All 22 photos and six ROM binaries match their acquisition manifests | Verified |
| Reproducible histogram, must-target set, window search, subroutine walk and condition table | `analyze.py`; exact replay of `analysis.json`, ranking, graph and listings | Verified |
| Recovered-field mapping with status | `sequencer.json` plus named datapath variants | Verified as data-derived fields and hypotheses, not traced wiring |
| 1,024-word listing, remaining bits, control flow and dispatch tables | Original generated listing/graph and consolidated annotated listing/catalog | Verified |
| Resolve 01E and re-score | 01C pushes 01D; 01E consumes the frame; saved window and B0/B9 scores reproduce | Explained under the sequencer hypothesis |
| Every used word reachable or an explained exception | 999 default graph words; 22 causal entry-policy explanations and replayed reset witnesses | Explained exceptions retained; alternate policies are not silently merged |
| Real 8X02 with constant, per-select and random conditions | Executor modes, component tests, historical condition-mode runs, current random sweep/long run | Implemented and exercised |
| Scenario-indexed tables inferred from structure | Per-site table configuration, local-case/ROM-table studies and marked listings | Implemented; bases/index sources remain explicit hypotheses |
| Coverage and four-entry stack diagnostics; clean long sequencer runs reaching most of the store across random runs | Current one-million-cycle run and 128-seed sweep, exact replays | Execution criterion passes |
| Recover and score Am2901 alternatives using register patterns, loop behavior, instruction statistics and reversed chip-10 immediate hypothesis | Reproduced initial ranking; register-field, Q-independent and preparation studies; six named alternatives | Implemented; short list remains provisional |
| Use sine ROM and DAC as constraints | Sine-byte operand controls; DAC byte-width and buffer experiments | Implemented as explicit experiments; no unique physical assignment |
| Integrated slices/sequencer with selectable flags and logged external world | `execute.py`, component tests, current q2/q3 traces | Implemented |
| Datapath-derived dispatch when suggested | Q and preceding-Y index policies; nonzero masked nested reset study | Demonstrated with real caller stack; other sites may remain scenario-driven |
| Millions of clean integrated instructions and stable inspectable activity | Two million primary integrated instructions plus exact full replays; q3 live ROM feedback | Execution criterion passes |
| Name subroutines and annotate from traces | 534 used words annotated; 23 of 37 cataloged direct-call entries have annotations | **Incomplete: 14 direct-call entries still unannotated** |
| Relate I/O to sine lookup, DAC, sample timing and controller exchange | Live sine input; hypothetical DAC sink; measured instruction counts; separately verified 8031 frame/handshake routines | **Partial: no complete controller/microcode or recurring sample transaction yet** |
| Feed routine evidence back into mapping/execution | Q-independent alternatives, source-register comparisons, carry/flag timing and handler studies | Implemented, ongoing where interpretations disagree |
| Optional continuity checks | Prioritized in the plan and board worksheets | Optional; not an execution or interpretation blocker |

The 22 graph exceptions have specific paths and policy causes in
[ENTRY-POLICY-AUDIT.md](ENTRY-POLICY-AUDIT.md). Their default listing status
continues to say the entry is unresolved under that default policy. This is
compatible with explaining an exception; it is not a claim that one globally
safe hardware decode has been recovered. The union-reaching relaxed graphs
still expose a possible stack underflow at 2FF.

## Remaining work

The catalog identifies these unannotated direct-call entries:

```
04C 06F 09A 112 131 228 238 240 270 2EC 335 357 366 370
```

They are the next concrete routine-reading queue. There are also unannotated
branch/case bodies; 534/1,021 is an annotation count, not a percentage of
understood modem functionality. Annotating these entries alone would not prove
that all of step 5 is finished.

The external-interface work needs a coherent transaction that relates data
production, buffering, transfer, repetition and controller interaction under
stated assumptions. Independently replaying 65 reset phases is not evidence of
autonomous phase advance. An unknown physical clock may remain a parameter;
assigning an arbitrary frequency does not establish a recurring sample path.
Likewise, a verified four-byte controller frame is not by itself a DSP command.
These are software/evidence tasks, not a demand for continuity measurements
before continuing.

## Reproduce

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/plan_validation.py --out /tmp/nokia-plan-validation
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -p 'test_*.py'
```

The runner's execution gate requires clean complete runs, maximum depth at most
four, no unused words, exact full replays and unchanged saved prefixes, at least
one million sequencer and two million integrated primary instructions, and at
least 90% clean random-sweep coverage. Tests reject failed, truncated,
non-reproducible, over-depth and insufficient-coverage summaries. The 106-test
suite passes. No full-plan completion flag is inferred from this execution gate.
