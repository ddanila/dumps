# Downstream use of surviving preparation data

Survival at 195 does not by itself establish a useful data path. Following
each surviving location to its first possible read or replacement separates
unused values from values that actually affect later arithmetic. Both register
assignments still have a viable local use, but in different candidates and
on different branches.

## First accesses under the declared control flow

The analysis starts at 195 with empty stack and the saved ROM-backed dispatch
edges. Each profile explores 192 stack-aware control states without exceptions.
All declared branch outcomes and table targets are included. A path stops at
the first read of the tracked location or an instruction replacing it.

| Candidate and roles | Location | First possible read | Replacement without prior read |
| --- | --- | --- | --- |
| 23,27,31 original | Q | 1E0, if 195 branches | 196, if 195 falls through |
| 31 original | R2 | None | 19E |
| 07,23,27,31 swapped | R10 | None | 19E |
| 07,27 swapped | R12 | None | 1B5 |
| 23,31 swapped | R12 | 1A1 | None before that read on explored accessing paths |

This refines the [alternate-caller result](SINGLE-CALLER.md): swapped 07's
surviving R10 is not a demonstrated downstream operand. The broader comparison
finds a different swapped candidate whose R12 is used. Original-role Q is also
used, while its accompanying R2 value is replaced without a modeled read.

Reads include selected ALU operands, the special A-to-Y destination mode, and
Q's own shift input. Reads occur before writes in the same instruction, so a
read-modify-write counts as a use. A replacement counts even if it stores the
same numerical value. The graph retains the full return-stack context.

A selected operand may be masked by the other operand or ALU function. These
are therefore potential uses, not numerical-dependence proofs. Cycles without
access may persist, so a possible read does not imply every execution reaches
it. Unknown external consumers, different control edges, and register decodes
are outside this analysis. It refuses to proceed if the graph is truncated
or reports an exception.

## Two concrete continuation traces

Both witnesses rerun the full caller from 18B, preserving actual datapath and
carry state across 195. They compare zero preparation bytes with 12,34,56,78
(hex), use Q=0, zero initial RAM, external D=0 after preparation, one transform
iteration, and condition mask 7 inside 270. Neither injects a register value
at 195 or counts toward reset coverage.

**Original-role candidate 31, entry 0, branch at 195 taken.** Preparation leaves
Q=87 rather than 00 at 195. Instruction 1E0 computes Q−1 with the active carry
policy: Y=86 rather than FF. At 1E1, D+Q writes R4=87 rather than 00. Execution
continues through 1E4's branch to 19C. There R0, R2 and R4 differ, and Q still
holds 87. The complete local run takes 57 instructions with balanced stack.
This is direct evidence of a preparation-dependent internal arithmetic result
under this candidate, beyond mere register survival.

**Swapped-role candidate 31, entry 1, branch at 195 not taken.** Explicit TSK
choices at 196 and 19A skip 197 and 19B. The third preparation byte survives
as R12=56 rather than 00 through 1A0. At 1A1 the ALU selects A=R12 and Q,
computing `A + ~Q + carry`; Y becomes 55 rather than FF. The run stops before
1A2 after 62 balanced instructions. No physical recipient is assigned to this
ALU output, and the result does not establish the purpose of the routine.

Thus the current evidence supports two different internal-use paths. It does
not select a physical wiring map, justify calling either one demodulation, or
establish an external write. The next useful constraints are the meaning of
the branch at 195, the later use of the arithmetic results, and the unresolved
external read/write controls.

## Reproduce and verify

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/first_use_study.py \
  --out /tmp/nokia-first-use-study
```

[Configuration](first-use-search.json),
[first-access paths and decoded instructions](results/first-use-study/summary.json),
[original-role trace](results/first-use-study/witness-original.json), and
[swapped-role trace](results/first-use-study/witness-swapped.json) preserve the
assumptions and evidence. All three artifacts reproduce byte for byte. The
functional/assumption suite passes 53 tests, including read-before-write,
replacement barriers, A-output reads, and Q-shift reads. The full plan remains
incomplete.
