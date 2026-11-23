# Read the program by address

The [annotated listing](results/program-reading/listing.csv) consolidates the
current control-flow graph, six candidate datapath decodes, and evidence-linked
routine interpretations for all 1,024 words. The [catalog](results/program-reading/catalog.json)
records direct-call entries, dispatch targets, unresolved addresses, and source
file hashes. These are generated indexes of existing evidence, not a new
hardware model or a claim that the full program has been understood.

## Reading the columns

- `pc`, `raw`, `command`, `select`, and `direct` give the shared sequencer decode.
  `encoded_target` is the decoded address field even when the instruction does
  not use it as a target. For computed transfers, consult `dispatch` instead.
- `dispatch` preserves the complete scenario table, including repeated indices,
  ROM lookup metadata where present, and its assumption/evidence labels.
- `direct_callers` lists calls that actually use the encoded direct target under
  this scenario. Calls overridden by explicit dispatch tables are excluded.
- Each profile has an `operation` column with its ALU expression, A/B register
  numbers, mapped carry bit and carry-feedback selector. Carry policy remains
  an assumption; these columns do not turn a branch-address byte into a proven
  immediate operand.
- Each profile also has a `labels` column. A name appears only in profiles
  supported by its annotation. `annotations` contains the full meanings,
  profile scopes, limitations, and evidence-document paths relative to this
  directory. Blank labels mean no curated interpretation is supplied.
- `explanation_status` distinguishes reachable code, unresolved entry paths,
  and the three all-FF unused words. A local arithmetic interpretation does
  not change an unresolved entry into an explained exception.

`q1` through `q4` are the [Q-independent candidates](Q-INDEPENDENT.md).
`fitted_original` and `fitted_swapped` are the mappings in the selected
[reset-to-preparation examples](SELECTOR-COMPLETION.md). Their source fields
and register roles differ from the four earlier profiles. The generator
requires all six profiles to share the sequencer decode before combining them
into one address listing.

## Current provisional names

| Addresses | Interpretation | Principal limitation |
| --- | --- | --- |
| 01C–01F | Call-fed loop entry | Control-flow explanation, not a counted-loop algorithm |
| 078–084 | Terminal tail | Physical completion and restart unknown |
| 085–089 | Register right-shift helper | Not established as serial output |
| 18D, 19C | Successor-byte wait preparation | Tested original-role reset path only |
| 1EC–1EE | External-byte equality poll | Previous-zero condition and external channel remain hypotheses |
| 1E9–1EB | Conditional Q drain | Current versus previous zero flag changes iteration count |
| 341–344 | Preparation with disputed register roles | External operand and destination roles remain hypotheses |
| 379–388, 392–3A1, 3AB–3BA | Paired add/subtract and permute | Output slots are virtual |
| 3C5–3D4, 3DA–3E9 | Paired quarter-turn transform | Identities were search constraints; nonzero evidence is local |
| 3EF–3FE | Source-overlapping transform | Cannot reuse the independent quarter-turn formula |
| 2BC–2C5 | Nested computed-call wrapper | Needs site-scoped dispatch assumptions |
| 187–18A | Input-matched left shift | Constant nonzero D can prevent return after Q reaches zero |
| 36C–36E | Carry-controlled three-add loop | Middle versus last carry depends on flag timing; external operands unknown |
| 109 | Input-code dispatch candidate | Optional current-Y index; physical source and later-entry preconditions unknown |
| 248–24E | Three-loop shift wrapper | Does not establish R7; each loop has separate input-dependent termination |
| 296–29E | Input-dependent biased Q shift | Most constant-input cases with R7=FF repeat under the selected previous-flag policy |
| 2D0–2D8 | Paired Q drains | Previous-zero policy; transient output meaning unknown |
| 256–257 | Conditional adjustment selector | Entry from reset and condition meaning unknown |
| 2D9–2DE | Transient one-unit adjustment | No surviving internal effect or identified output consumer |
| 008, 26F, 21F, 2C4 | ROM-backed dispatch candidates | Site/bank/range/index associations remain hypotheses |

These annotations cover 184 used words, including overlaps and disconnected
local probes. That count is not a measure of understood modem functionality.
The catalog additionally lists direct-call entry points with linear-walk
boundary hints; a linear walk is not a complete routine control-flow analysis.
Unannotated operations and remaining routine meanings stay open.

## Coverage stays separated

| Listing column | Evidence | Used words |
| --- | --- | --- |
| `static_reachable` | Combined local-case graph | 999 |
| `sequencer_sweep_visited` | Its fixed 128-seed sequencer sweep | 941 |
| `reset_original_visited` | Selected fitted original-role reset example | 187 |
| `reset_swapped_visited` | Selected fitted swapped-role reset example | 186 |

The two reset examples use different datapath/condition hypotheses from the
sequencer sweep. These columns are not merged into a single execution claim.
For example, 2D9 has a tested local interpretation but remains statically
unreachable in the selected reset graph. All 22 disconnected words remain
explicit in the catalog.

## Reproduce

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/program_reading.py \
  --out /tmp/nokia-program-reading
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -p 'test_*.py'
```

[Annotation manifest](program-reading.json) owns every curated label and its
scope. The generator validates evidence paths, profile names, address ranges,
shared control decode, and consistency of the saved sweep with a freshly
computed graph. Both output files reproduce byte for byte. All 61
functional/assumption tests pass, including checks that interpretation labels
do not leak across profiles or hide unresolved entries. The full plan remains
incomplete, particularly physical I/O and broader algorithm interpretation.
