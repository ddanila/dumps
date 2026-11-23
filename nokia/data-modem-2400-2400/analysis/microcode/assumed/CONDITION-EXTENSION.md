# Extending the fitted condition policies

The two local previous-flag policies run cleanly over the tested broader
profiles, but they do not yet explain reset-to-preparation execution. None
of the 256 reset-started cases reaches 341. The two million-cycle reset
examples spend 999,958 cycles at 084 and never sample the preparation inputs.
These runs validate bounded execution under the scenarios, not useful signal
processing or the fitted condition wiring.

A [free-selector completion follow-up](SELECTOR-COMPLETION.md) now supplies
a reset-to-preparation path by asserting previously unconstrained selector 5,
without changing the fitted flag sources.

## Profiles and measurements

[condition-extension.json](condition-extension.json) keeps the fitted flag
sources and polarities unchanged. Each mapping runs with:

- The witness's historical target tables or the newer ROM-backed call/branch
  tables. Only target associations change between these profiles.
- Reset entry 000 or diagnostic local entry 18B. These results stay separate.
- Initial Q=00,01,80,FF; register RAM remains zero.
- Preparation bytes all zero, 12/34/56/78, all FF, or 55/AA/55/AA.
- Constant dispatch index 0,1,2,3, applied to every table in that run.

This gives eight profile groups of 64 runs each, 512 total. Each run executes
1,000 instructions. All finish without stack violations. Aggregate distinct
words per profile are:

| Register roles | Target hypothesis | Start | Words visited |
| --- | --- | --- | --- |
| Original | Witness | 000 | 123 |
| Swapped | Witness | 000 | 123 |
| Original | ROM-backed | 000 | 62 |
| Swapped | ROM-backed | 000 | 62 |
| Original | Witness | 18B | 166 |
| Swapped | Witness | 18B | 156 |
| Original | ROM-backed | 18B | 187 |
| Swapped | ROM-backed | 18B | 187 |

All 256 local-entry cases visit preparation, as expected from their entry
point. None of the reset cases does. The local visits are not evidence that
the scenario reaches this routine from reset. Changing PC-keyed bytes at an
unvisited routine cannot test the reset execution's response to those bytes.

The witness-target profiles all finish in the 084 self-loop. ROM-backed reset
profiles may instead remain around 060/062; some original-role local profiles
finish around 1EC/1ED. Final-PC counts are saved in each report. These endpoints
are not identified hardware wait states merely because the emulator remains
there.

## Unknown flags that actually affect decisions

The main runner logs condition evaluation even on instructions that do not
consult TEST. This study separately counts unknown sources only at TSK, BLT,
conditional BSR and conditional BRT; unconditional transfers are excluded.

Sixteen of the 64 original-role, ROM-backed reset runs use unknown preceding
flags at real decisions. PCs 015 and 01E each contribute sixteen unknown
reads. The scenario supplies its explicit fallback, so execution continues;
these branches are not verified evaluations of the corresponding physical
flags. Other tested profile groups have no unknown decision-source reads.
This count does not include the separate arithmetic carry-feedback fallback.

Thus a global fit cannot be inferred from the short witnesses, whose consumed
condition flags were known. The broader result identifies exact instructions
where the component's missing logical-flag semantics matter.

## Million-cycle reset examples

Both examples use ROM-backed targets, Q=00, marked preparation bytes, constant
index 1, and the respective fitted policy. Each executes one million cycles
cleanly, visiting 43 used words (4.21%). Both enter 084 after 42 instructions
and stay there for the remaining 999,958. Neither reaches 341. Complete inputs,
summaries and bounded 1,000-record traces are saved.

These examples do not replace the earlier 91.97% coverage experiment: its
scenario-driven conditions and dispatch choices are different. No coverage
is merged across those incompatible hypotheses.

## Implications

The selected previous-flag policies are adequate for reproducing the local
numerical-use paths and for the tested stack-safe continuations. They are not
yet an explanation of how startup supplies those paths. Unobserved selectors
still use constant-zero stubs, dispatch uses one fixed index for all sites,
and external data remains a PC-keyed fixture. Those explicit choices may
restrict access to 18B; this study does not prove a wiring contradiction.

A useful next test is to vary the previously unconstrained selectors while
preserving the fitted ones, rather than treating more cycles in the same
self-loop as progress. Physical I/O and routine-level modem semantics remain
unresolved. The full plan is incomplete.

## Reproduce and verify

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/condition_extension.py \
  --integrated-cycles 1000000 --out /tmp/nokia-condition-extension
```

[Summary](results/condition-extension/summary.json),
[original ROM-backed reset sweep](results/condition-extension/original-rom_calls-000.json),
[original million-cycle example](results/condition-extension/integrated-original/summary.json),
and [swapped million-cycle example](results/condition-extension/integrated-swapped/summary.json)
retain the observations. The nine sweep reports regenerate byte for byte.
The functional/assumption suite passes 56 tests, including separation of
unknown flags used for decisions from incidental TEST values on other
instructions. Local entries remain excluded from reset coverage.
