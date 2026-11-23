# Reset reaches preparation when unconstrained selector 5 is asserted

The constant-zero defaults on selectors absent from the local fit were
restricting startup. Setting selector 5 to constant one, while preserving
every fitted flag source and polarity, lets both candidates reach 18B and
341 from reset. The selected original-role example then shows preparation
bytes affecting a later branch and the number of shift-loop iterations.

This is a coherent reset-started execution under explicit input and dispatch
hypotheses. It is not recovered hardware wiring, a complete modem boot, or
proof that the physical selector 5 is a constant signal.

## Search and preserved constraints

[selector-completion.json](selector-completion.json) enumerates all sixteen
constant completions of the four unobserved selectors in each fitted policy:

- Original roles: selectors 1,4,5,6 are free; 0,2,3,7 retain their fitted flags.
- Swapped roles: selectors 1,2,4,5 are free; 0,3,6,7 retain their fitted flags.

Each completion uses both historical and ROM-backed target hypotheses,
initial Q=00/55, and constant dispatch index 0–3. RAM starts at zero and
preparation uses the marked PC-keyed bytes 12,34,56,78. This gives 256 runs
per mapping, 512 total, each 1,000 instructions from reset. All are clean.

| Roles | Runs reaching 18B and 341 | Conditions shared by reaching cases |
| --- | --- | --- |
| Original | 32 | Selector 5=1, index 2 |
| Swapped | 16 | Selector 5=1, selector 2=0, index 2 |

These patterns describe this finite sweep only. Both initial Q values and
both target hypotheses have reaching cases. No fitted selector was changed.
The chosen examples prefer the ROM-backed profile and then the smallest
completion mask, initial Q and entry. That is deterministic witness selection,
not a hardware-confidence ranking.

## The reset path and data-dependent behavior

Both selected examples differ from the previous defaults only by selector
5=1. At cycle 3, instruction 003 branches to 100 instead of falling through
to 004. Fixed index 2 at the later dispatch selects 10C, which branches to
18B. The caller executes at cycle 37 and preparation starts at cycle 38.

With original register roles, the marked input reaches Q=87 at instruction
195. The fitted previous-flag policy takes its branch, and 1E0 computes a
preparation-dependent result. The first control-flow difference between zero
and marked preparation inputs occurs at cycle 104, BLT at 1EA:

| Preparation bytes | Next PC at cycle 104 | First 1E9 loop iterations |
| --- | --- | --- |
| All zero | 1EB, exit | 1 |
| 12,34,56,78 | 1E9, repeat | 9 |

After each marked-run shift, Q is 43,21,10,08,04,02,01,00,00 (hex). The ninth
iteration is significant: the fitted policy tests the preceding instruction's
zero flag, which describes the unshifted ALU result at 1E9. It exits one
iteration after the shift first makes Q zero. The earlier local eight-iteration
fixture used the current flag and is a different timing hypothesis.

Neither selected zero/marked trace consumes an unknown condition flag at a
real decision in its first 1,000 instructions. Arithmetic carry fallback is
still a separate explicit model assumption. The first modeled data difference
is at 341, where the zero-input ALU result is 00 and the marked result is EE.

For the selected swapped-role example, zero and marked inputs follow the same
PC path throughout the saved prefix and both exit their first shift loop in
one iteration. They reach the same final internal state. This example uses
entry 2; it does not invalidate the separate entry-1 R12-use witness.

## Progress and remaining limits

The marked original-role example visits 187 used words; the swapped example
visits 186. Both finish the 1,000-cycle run at 084. The original zero-input
comparison instead finishes near the 1EC/1ED loop. Input-dependent branching
therefore does not yet imply useful continuing signal processing.

The two million-cycle examples extend the selected marked scenarios and
finish cleanly with maximum stack depth three. Original roles spend 999,778
cycles at 084; swapped roles spend 999,795 there. Saved mappings, scenarios,
summaries and bounded traces preserve the startup activity. More repetitions
of the final loop add no new algorithmic understanding.

The result closes one specific gap: there is now a reset-to-preparation-to-
computation example with consistent per-selector policies and an observable
input-dependent loop decision. Fixed dispatch indices, PC-keyed external bytes,
remaining constant selectors, incomplete logical flags and physical I/O still
prevent interpreting it as faithful board execution. Coverage remains far
below the earlier scenario-driven 91.97% result, which is not combined with
this experiment. The full plan remains incomplete.

## Reproduce and verify

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/selector_completion.py \
  --integrated-cycles 1000000 --out /tmp/nokia-selector-completion
```

[Summary](results/selector-completion/summary.json),
[original marked reset trace](results/selector-completion/original-marked/trace.jsonl),
[original zero-input comparison](results/selector-completion/original-zero/trace.jsonl),
and [swapped marked trace](results/selector-completion/swapped-marked/trace.jsonl)
preserve the evidence. The functional/assumption suite passes 57 tests,
including a check that completing free selectors leaves every fitted source
and polarity unchanged and does not mutate the original scenario. Sweep
reports and selected short replay artifacts reproduce byte for byte.
