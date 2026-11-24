# Verified reset witnesses for the default graph gaps

Five saved integrated runs cover all 22 used words outside the default
999-word graph. `reset_witness_catalog.py` replays every run and indexes the
first observed entry into each gap. The [annotated listing](PROGRAM-READING.md)
now links those entries directly to their named mapping and scenario.

This is a union of **three mappings and five scenarios**, not a single model
with complete runtime coverage. The default graph and its unresolved-entry
labels remain unchanged. Two witness scenarios still have conservative stack
errors, and the diagnostic inputs do not establish physical hardware wiring.

| Witness ID | Mapping | Default-gap words observed | First 084 cycle | Conservative graph exceptions |
| --- | --- | --- | ---: | ---: |
| q3-masked-ff | q3 | 2D9–2DF | 283 | 20 |
| swapped-qzero-ff | fitted_swapped | 0FA, 0FD–0FF | 144 | 2 |
| q2-reentry-fc | q2 | 256–258 | 187 | 0 |
| q3-differences-01 | q3 | 287–28A, 3BD–3BF | 158 | 0 |
| q2-zero-q | q2 | 2CF, 2D9–2DB | 137 | 0 |

The first run has 512 recorded cycles; each other run has 256. All start with
PC=0, RAM zero and Q zero, execute cleanly through their full recorded bounds,
and end at 084. The list is a curated cover, not a claim of a minimum possible
witness set. Several entries have more than one supporting run.

## What the verifier checks

The [manifest](reset-witnesses.json) owns each ID, profile, artifact directory,
evidence document and limitation. For each witness the verifier:

1. Requires a hypothesis label, evidence and limitations, and checks that the
   saved mapping equals the named profile.
2. Requires zero reset, integrated mode, clean completion, no unused-word
   execution and no stack underflow/overflow in that run.
3. Matches the saved mapping/scenario digests and requires a full trace with
   consecutive cycle numbers from reset.
4. Re-executes the saved mapping and scenario with the recorded seed and cycle
   count. The mapping, scenario, summary, full trace and I/O log must reproduce
   byte for byte under the current emulator.
5. Derives first visits from the trace, reconstructing RAM and Q before each
   target instruction and recording its live stack depth, test and next PC.
6. Checks trace coverage against the summary and requires coverage of every
   gap derived from the current default graph. Missing evidence is an error.

The report also recomputes each witness scenario's conservative graph and
retains its exceptions. A clean run does not erase unsafe alternative paths.
The validation tests reject an actual failed q3 run, a truncated trace, an
altered register value, a mismatched profile and an incomplete witness set.

## Reading the generated artifacts

The standalone [report](results/reset-witness-catalog/report.json) contains
`entries` indexed by hexadecimal PC, the five witness descriptions, exact
first-entry state and source hashes. For example, the 2DF entry points to the
q3 FF run with its state at cycle 196; its associated scenario still carries
the 20 conservative stack exceptions discussed in [LAST-ENTRY.md](LAST-ENTRY.md).

`program_reading.py` performs the same replay verification when generating
the main listing. Its new `reset_hypothesis_witnesses` column gives the ID,
profile and first cycle for each default-gap word. The main catalog embeds
the complete report as `reset_hypothesis_catalog` and verifies that its
baseline scenario and profiles agree with the listing.

An empty witness cell (`[]`) on a word already reachable in the default graph
means it is outside this gap-focused index, not that the word has never been
executed. The existing `static_reachable`, sequencer sweep and original/reset
example columns retain their independent meanings. `explanation_status`
continues to describe the default graph; a witness under an alternative gate
does not silently change that status.

## Reproduce

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/reset_witness_catalog.py
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/program_reading.py
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -p 'test_*.py'
```

Both generators replay the five saved runs rather than trusting their summary
flags. The standalone and embedded catalogs reproduce exactly. This makes
the reset-entry evidence reviewable in the plan's main listing; broader
algorithm interpretation, physical I/O and general model validity remain
open, so the full plan is not complete.
