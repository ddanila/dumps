# 2FD–2FF requires an incoming return frame

The [complete-entry policy audit](ENTRY-POLICY-AUDIT.md) always retained a
possible stack underflow at 2FF. Fixing the known constant condition selectors
does not remove it. The local structure explains why: 2FD–2FF is a computed-call
wrapper with a return to its own caller, not a standalone completion path.

## Constant selectors do not eliminate the path

The shortest free-condition graph witness uses select 1 at 2E3 to skip to
2E5. That skip is inconsistent with the retained previous-flag scenario,
where select 1 is constant false. The audit is repeated with every constant
selector fixed to its declared value and only actual flag selectors left free.

The constrained graph reaches 805 words and still reports the 2FF underflow.
Its 114-instruction path instead takes:

`255 → 256 → 257 → 2DC → 2DD → 2DE → 2DF → … → 2E3 → 2E4 → 3BB → 3BC → 2FD`.

The path is replayed on the real sequencer with an empty live stack on entry
to 2FD. It is a control-flow witness with flag choices, not a claim that the
entire prefix satisfies one datapath input schedule. The three instructions
at 2FD–2FF then have this structure:

- 2FD exposes a transient ALU result and advances without pushing a frame.
- 2FE calls 21A, pushing the return address 2FF.
- When 21A returns, that newly pushed frame is consumed. 2FF must pop the
  **pre-existing caller frame**.

Changing data inside 21A cannot supply a missing caller frame after its normal
balanced return. A route that never returns can avoid the eventual underflow,
but does not establish successful completion.

## Stack-depth contract under the retained dispatch tables

The local conservative graph is explored from 2FD for every possible entry
depth. Analysis-only sentinel addresses distinguish return to a caller from
ordinary control-store addresses; no emulator stack is repaired or seeded in
a claimed reset run.

| Incoming depth | Reachable local words | Conservative exceptions |
| --- | ---: | --- |
| 0 | 44 | Underflow at 2FF |
| 1 | 44 | None; caller return reachable; maximum depth 4 |
| 2 | 42 | Overflow possible at 223 or 2C4 |
| 3 | 8 | Overflow at 21F |
| 4 | 2 | Overflow at 2FE |

Exactly one incoming frame admits every modeled nested dispatch choice without
stack exceptions. This is a worst-case safety contract for the declared tables,
not proof of termination for every flag sequence. Shallower selected callees
can return with two incoming frames, but the nested alternatives can overflow.

Two existing full reset runs are replayed byte for byte as independent examples:

- The q2 seed-115 nested run enters 2FD with one frame. Its real nested calls
  reach depth four; 2FF later pops the remaining caller frame and returns to
  213. The complete run is clean.
- The q3 extended-gate D=00 run enters 2FD with no frame. Its call to 21A returns
  to 2FF, where the emulator reports `unknown stack at PC 2ff`. The failure is
  preserved and verified, not treated as a successful witness.

These examples use different mappings and scenarios. They demonstrate both
sides of the stack contract without asserting that the graph's complete-entry
policy is their common runtime configuration.

## The data guard before the tail

Under q3, 3BB computes and stores
`R5 = (old_R5 - R0 - 1) mod 256`. When 3BC is conditional and uses previous
zero with inverted polarity, it branches to 2FD unless
`old_R5 == (R0+1) mod 256`. All 65,536 R0/R5 pairs are checked against the ALU:
exactly 256 fall through. The default unconditional interpretation of 3BC
ignores this arithmetic predicate.

Instructions 2DF–2E4 preserve R0 and R5, even when their external bytes change Q.
Consequently, under the minimum entry relaxation (which leaves 2E4 an
unconditional jump to 3BB), those external bytes cannot repair a failing
R0/R5 guard. For an empty-stack entry with R0=R5=0, 3BB produces FF and 3BC
necessarily selects the return wrapper under previous-zero timing. This is a
local data-aware condition, not a proof that every reset reaches that state.

The broader diagnostic gate in [LAST-ENTRY.md](LAST-ENTRY.md) can instead let
2E4 fall through to a different masked-input test at 2E5. That is a distinct
policy and path; its successful FF case does not validate the minimum
seven-site policy. A safe interpretation must explain both the caller-frame
requirement and which path is selected, rather than patching the final POP.

## Evidence and scope

[Configuration](tail-stack-contract.json), [runner](tail_stack_contract.py), and
[report](results/tail-stack-contract/report.json) retain the constrained path,
five local depth analyses, arithmetic counts, both replayed witness summaries,
and source hashes. The report reproduces exactly. The 98-test suite checks the
stack-depth boundary, constant selector, guard arithmetic and preserved failing
reset trace.

The listing gains a computed-call return-wrapper interpretation at 2FD–2FF
and a q3 difference guard at 3BB–3BC, bringing annotated coverage to 366 used
words. This explains a calling convention and a hazard; it does not recover a
universally safe hardware gate or complete the wider algorithm/I/O work.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/tail_stack_contract.py --out /tmp/nokia-tail-stack-contract
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -p 'test_*.py'
```
