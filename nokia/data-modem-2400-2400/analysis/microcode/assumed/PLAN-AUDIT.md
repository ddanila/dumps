# Plan acceptance audit

The [plan](../PLAN.md) is **not yet complete**. Its execution requirements now
have a consolidated check against the current executor. Program interpretation
still has concrete gaps in branch/case interpretation and modem-function attribution.
All 37 cataloged direct-call entries now have scoped annotations.
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
| Unknown inputs become logged parameters | `execute.py` read policies, timed external condition line, flag fallback accounting, external-read trace records and captured writes | Implemented; stubs remain labelled |
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
| Name subroutines and annotate from traces | 691 used words annotated; 37 of 37 cataloged direct-call entries have annotations | **Direct-call catalog annotated; broader branch/case interpretation remains incomplete** |
| Relate I/O to sine lookup, DAC, sample timing and controller exchange | Replayed actual 8031 build/transmit, completion-qualified frame latch, declared byte routing, actual ROM operand and recurring DAC transfers with explicit relative clock ratio | Implemented as a one-way diagnostic hypothesis; physical routing and signal-processing purpose unresolved |
| Feed routine evidence back into mapping/execution | Q-independent alternatives, source-register comparisons, carry/flag timing and handler studies | Implemented, ongoing where interpretations disagree |
| Optional continuity checks | Prioritized in the plan and board worksheets | Optional; not an execution or interpretation blocker |

The 22 graph exceptions have specific paths and policy causes in
[ENTRY-POLICY-AUDIT.md](ENTRY-POLICY-AUDIT.md). Their default listing status
continues to say the entry is unresolved under that default policy. This is
compatible with explaining an exception; it is not a claim that one globally
safe hardware decode has been recovered. The union-reaching relaxed graphs
still expose a possible stack underflow at 2FF.

## Remaining work

All 37 cataloged direct-call entries have evidence-linked annotations, including
2EC's three paths through an actual nested return. This closes the direct-call
naming queue, not the whole program-reading step. Unannotated branch/case
bodies remain: 691/1,021 is an annotation count, not a percentage of understood
modem functionality. The next reading work must connect these bodies to the
existing handler contracts and distinguish scoped local evidence from reset
reachability and physical function. The largest currently unannotated listing
spans are 19D–1DE (66 words), 020–04B (44), 1EF–219 (43), 054–06E (27),
and 0DF–0F8 (26). These are contiguous listing spans, not inferred subroutine
boundaries; the catalog and traces should guide their decomposition.

The [controller-to-DAC bridge](FRAME-DAC-BRIDGE.md) now supplies a coherent
one-way transaction under the plan's assumption policy. It joins actual
controller construction/transmission, completion and latch ordering, microcode
input consumption, ROM lookup and recurring DAC load/transfer. Six complete
transactions and four rejected incomplete transfers are replayed by this audit.
The DAC updates recur every 12 microinstructions with constant held codes;
there is no claimed autonomous phase advance or controller return protocol.
Physical routing and clocks remain labelled assumptions, not additional
completion gates. The remaining reading work must explain broader handler/case
behavior and its computational role without treating this diagnostic connection
as recovered modem functionality.

## Reproduce

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/plan_validation.py --out /tmp/nokia-plan-validation
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -p 'test_*.py'
```

The runner's execution gate requires clean complete runs, maximum depth at most
four, no unused words, exact full replays and unchanged saved prefixes, at least
one million sequencer and two million integrated primary instructions, and at
least 90% clean random-sweep coverage. Tests reject failed, truncated,
non-reproducible, over-depth and insufficient-coverage summaries. The 119-test
suite passes. No full-plan completion flag is inferred from this execution gate.
