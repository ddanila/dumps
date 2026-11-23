# The D0/D1 ROM tail and the nested computed-call wrapper

Ten previously disconnected words, 2BC–2C5, can be reached using two more
actual Am27S31 bytes. The next bytes after the working 080–0CF range are
D0=B3 and D1=BC. With bank 200, they select 2B3 and 2BC. The latter is a
**nested computed-call wrapper**: it reaches call 2C4 and returns at 2C5.
That is a structural routine label; its datapath algorithm remains unknown.

Adding these entries without distinguishing the nested call exposes a stack
overflow. A site-scoped target hypothesis avoids it and reaches 993 of 1,021
used words statically. The 28 remaining words stay explicitly unresolved;
they are not relabeled as explained exceptions.

## Alternatives and counterexamples

All tables are reconstructed from the hash-checked ROM bytes, retaining
repeated entries and their indices. No stack repair or synthetic return is
used. The compared ranges below all use target bank 200:

| Variant | Outer call 21F | Nested call 2C4 | Static words | Exceptions |
| --- | --- | --- | --- | --- |
| Baseline | 080–0CF | 080–0CF | 983 | None |
| Outer tail | 080–0D1 | 080–0CF | 993 | Overflow at 223 |
| Both tails | 080–0D1 | 080–0D1 | 993 | Overflow at 223 and 2C4 |
| Scoped row | 080–0D1 | 090–0CF | 993 | None |
| Scoped byte | 080–0D1 | 081–0CF | 993 | None |

The outer-tail overflow has a concrete stack-context path. When 21F executes
with two frames already present, calling 2BC creates a third. Its nested 2C4
call can select 221, creating a fourth. The direct call at 223 then attempts
a fifth push. In the both-tails alternative, 2C4 can additionally select 2BC
again, allowing recursive nesting. Shortest graph witnesses are saved.

The scoped variants remove 221 from the inner target set and do not let that
inner call recursively select 2BC. This is a constraint on independent scenario
choices, not evidence that the board uses the proposed slices. Excluding only
byte 080 produces the same inner target set as excluding the whole 080 row,
although repeated-entry frequencies and indices differ. The stack evidence
therefore **does not determine the exact inner ROM range**.

The 82-byte outer range also remains a boundary hypothesis: D0/D1 may belong
to a short sixth row while D2 onward serves another role. Selecting every byte
of 0D0–0DF as a call table was already rejected in the earlier study. This new
experiment does not erase that counterexample or establish a row decoder.

## Execution and the first observed 2C4 path

The scoped-row candidate is executed with the existing scenario-driven
conditions and dispatch indices. The fixed 128-seed suite, 1,000 cycles per
seed, is clean and reaches 939 distinct words (91.97%). This equals the prior
coverage count; it is not claimed as a dynamic coverage improvement. None of
those 128 seeds exercises the new nested call.

A separate bounded witness search finds seed 334. It is excluded from the
fixed-suite coverage. Its real-ROM sequencer trace contains:

| Cycle | Site | Proposed ROM address | ROM byte | Selected target |
| --- | --- | --- | --- | --- |
| 105 | 26F | 0F9 | 00 | 200 |
| 159 | 21F | 0D1 | BC | 2BC |
| 168 | 2C4 | 091 | 2D | 22D |

The run completes 1,000 cycles cleanly, reaching maximum stack depth four and
ending with depth zero. The reconstructed lookups match the actual executed
targets. They are candidate address-path logs, not physical bus observations.
This is sequencer execution; it supplies no new claim about arithmetic or I/O
inside 2BC–2C5.

## Audit of the remaining disconnected words

The [baseline catalog](results/rom-tail-study/unresolved-catalog.json) records
all 38 original disconnected words, their preceding instruction, unconditional
transfer status, and raw direct references with reference reachability and
any scenario override noted. Ten gain an entry under the scoped alternatives.
The remaining groups are:

| Words | Structural observation; still unresolved |
| --- | --- |
| 03A | Disconnected instruction before the reachable low-handler continuation |
| 03F | Previously considered third entry at local branch 03C; excluded by the current two-entry hypothesis |
| 0FA, 258, 2CF, 2DF | Individual instructions after decoded unconditional transfers; no entry in the current graph |
| 0FD–0FF, 256–257, 2D9–2DE | Branch fragments referencing one another and leading toward the common terminal tail; their incoming roots remain disconnected |
| 34F–352 | Possible third path after the two-entry 34C dispatch; not promoted from adjacency alone |
| 3BD–3BF, 287–28A | Disconnected chain: 3BF directly branches to 287 |

These facts narrow the missing-entry questions but do not explain why the
hardware executes or omits those words. In particular, a word following an
unconditional branch is not necessarily dead code; it may have an undiscovered
indirect entry. No artificial entry is added to claim complete reachability.

## Reproduce and verify

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/rom_tail_study.py \
  --out /tmp/nokia-rom-tail-study
```

[Configuration](rom-tail-search.json), [summary](results/rom-tail-study/summary.json),
[scoped-row scenario](results/rom-tail-study/scenario-scoped_tail.json), and
[witness trace](results/rom-tail-study/witness/trace.jsonl) preserve the inputs
and observations. All 17 artifacts regenerate byte for byte. The functional/
assumption suite passes 58 tests, including the outer-tail overflow, recursive
inner-call overflow, and the clean site-scoped alternative. The existing
working ROM-backed scenario remains unchanged. The full plan is incomplete.
