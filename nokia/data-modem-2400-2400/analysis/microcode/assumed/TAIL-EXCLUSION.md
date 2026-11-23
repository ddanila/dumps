# Why the remaining gated tail cannot execute under q2

**287–28A are excluded from reset execution under the declared gated q2
scenario.** This is a compositional control/dataflow argument, checked by
`tail_exclusion_study.py`, rather than an inference from unsuccessful sweeps.
It permits arbitrary byte reads at every cycle and arbitrary choices among
all declared dispatch-table entries. It also excludes 281–286.

The conclusion is conditional on the q2 mapping, all-zero initial RAM/Q,
previous-flag conditions, the scenario's constant condition inputs, zero-fill
shifts, mapped/previous carry and the optional composed BRT gate. It does not
establish dead code on the Nokia board, does not apply to other retained
mappings, and does not resolve the default listing's physical entry questions.

## Covering every entry

The script regenerates the fixed-condition graph: 796 words and 1,229 stack
states, without graph exceptions or budget exhaustion. It projects its edges
onto instruction addresses and checks the complete predecessor sets used in
the argument. This projection can admit extra paths by forgetting stack
context; it cannot remove a real execution path. No handpicked path is used
as a substitute for the complete entry set.

287 has exactly two predecessors: fallthrough from 286 and a branch from 3BF.
288, 289 and 28A have only their immediately preceding tail word as an entry.
Excluding both entries into 287 therefore excludes all four words.

## Entry through 286

Every path to 286 passes through the straight sequence 281–286. The only
entry into 281 is a taken branch at 200, and the only entry into 200 is the
computed branch at 26F.

Under q2, 26F computes zero AND Q without storing it. Its zero flag is always
set, independently of Q or any external input. Gated 200 tests inverted
previous zero and must fall through to 201. It cannot branch to 281.
The script verifies the exact decoded operation and its zero flag for all
256 Q bytes. This excludes the entire 281–286 sequence.

This is the flag dependency missing from the earlier shortest structural
witness `26F → 200 → 281 → … → 287`.

## Entry through 3BF

All paths into 3BF pass through 3BC, which follows 3BB. A backward scan over
the complete projected graph finds all possible last writes to Q and R0
before 3BB. The scan stops at writes, and checks that no path reaches reset
without encountering a write.

| Value at 3BB | Possible last writers | Constraint |
| --- | --- | --- |
| Q | 2E1, 2F3 | Both compute zero AND R0 into Q, so Q=0 |
| R0 | 073, 074, 1CE | These produce only 00 or FF on the relevant reset paths |

The Q result is independent of incoming registers and flags. The script
checks both writers over all 65,536 incoming R0/Q pairs.

The R0 constraints require two separate arguments:

- **Reset setup at 073/074.** Complete predecessor checks link this setup to
  reset through 003→100→101→06F. R9 starts at zero and is not written along
  that prefix. 070 puts R9+1=1 into R0; 073 shifts it to zero. If 074 executes,
  its subtraction and the preceding carry produce FF. Both alternatives are
  checked with the actual datapath and carry model across all incoming Q
  bytes, and the exact operand/destination fields are checked.
- **Later write at 1CE.** Its only predecessor is 1CD, entered from 1EB or
  through 2D8 from 1EB. Neither intervening instruction changes Q. The only
  entry into 1EB is the exit of the 1E9/1EA right-shift loop. With previous
  zero and zero-fill shifts, exit requires Q=0. All 256 incoming Q bytes are
  checked through the actual sequencer/datapath loop. 1EB and 1CE each compute
  D AND Q into R0, preserving Q. Each operation is separately checked for
  every D byte and both carry inputs, so independently varying read bytes
  cannot change the zero result.

3BB changes R5, preserving R0 and Q. If 3BC branches away, it does not enter
this tail. If it falls through, the established pairs at entry are therefore
only (R0,Q)=(00,00) or (FF,00). The
[conditional-tail rule](DISPATCH-RANGE.md) sends both pairs through 3BF to
3C0, never to 287. The script replays both cases through the actual models.

As a scope check, it also tests all 256 R0 bytes with Q=0 at local tail entry.
The other 254 R0 values do branch to 287. Thus these instructions are not
inherently unexecutable: the exclusion depends on the reset-derived register
constraints, not merely on the local tail's instruction sequence.

## Consequences for further work

The [Q-input sweep](Q-DISPATCH.md) supplied integrated reset witnesses for
eight of the 12 words added by the optional gate. The other four now have an
explicit explanation for their absence under q2. More byte/index sweeps
within these same assumptions cannot reach them.

Their absence is evidence to compare against alternative datapath mappings,
condition wiring, initialization or dispatch targets. It is not evidence
that the real firmware intentionally contains dead code. The default graph
and its unresolved-entry labels remain unchanged, and the broader plan still
requires physical I/O and algorithm interpretation.

## Reproduce

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/tail_exclusion_study.py
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -p 'test_*.py'
```

The [report](results/tail-exclusion-study/report.json) records complete checked
predecessor sets, reaching writers, local check counts, representative tail
traces, source hashes and the argument's scope. Assertions fail if the checked
fields, graph structure or local invariants no longer hold. This is an
explicit checked argument, not a general-purpose formal verifier.
