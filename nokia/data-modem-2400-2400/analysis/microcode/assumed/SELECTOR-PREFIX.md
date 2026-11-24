# First-dispatch selectors depend on both mapping and input schedule

The first dispatch at 109 exposes substantially different selector values
under the six retained mappings. In q1/q3, two earlier input additions
accumulate in Q. Supplying the same byte everywhere restricts Q to even
values, but independently supplying those two reads reaches all eight
handler entries through Q-based indexing. This is a property of the input
fixture, not evidence that the other four entries are intrinsically absent.

The study compares actual reset prefixes, with zero initial RAM/Q and the
existing previous-flag and unconditional-transfer policies. It stops after
the selected branch word enters its handler; it does not claim completion
or useful processing inside that handler.

## Matched scalar-input comparison

For each mapping and D=00–FF, the early waits at 117/106 receive D then zero,
while every other read supplies D. Only the source at 109 varies among
scenario index 2, current Y, Q and previous Y. The complete trace before 109
is identical across those four choices for each mapping/input pair.

Let `nz(D)` be 0 for D=0 and 1 otherwise. Values below are bytes, with sums
reduced modulo 256:

| Mapping | R0 at 109 | Q | Current Y | Previous Y |
| --- | --- | --- | --- | --- |
| q1 | FF | 2D | 2D | 3D+nz(D) |
| q2 | FF | 00 | 01 | nz(D) |
| q3 | FF | 2D | 2D+1 | 3D+nz(D) |
| q4 | FF | 00 | 01 | nz(D) |
| fitted_original | FF−D | 00 | D+1 | 00 |
| fitted_swapped | D | 00 | 00 | 00 |

These equations are checked against every executed prefix. The selected
index is reduced modulo eight for the declared table:

| Mapping | Current-Y entries | Q entries | Previous-Y entries |
| --- | --- | --- | --- |
| q1 | 0, 2, 4, 6 | 0, 2, 4, 6 | All eight |
| q2 | 1 | 0 | 0 for D=0; otherwise 1 |
| q3 | 1, 3, 5, 7 | 0, 2, 4, 6 | All eight |
| q4 | 1 | 0 | 0 for D=0; otherwise 1 |
| fitted_original | All eight | 0 | 0 |
| fitted_swapped | 0 | 0 | 0 |

The scenario source selects entry 2 in every case. Each q1/q3 parity-restricted
entry occurs 64 times. Their preceding-Y source selects entry 0 in 33 cases,
entry 1 in 31 cases, and each other entry in 32 cases: D=0 is the exception
to the otherwise affine `3D+1` expression. Fitted-original current Y selects
each entry 32 times, consistent with the earlier
[original-role study](DISPATCH109.md).

For q2/q4, changing the scalar input byte does not give current Y an eight-way
selector in this prefix. That limitation remains visible instead of being
hidden by the freely supplied scenario index. It does not prove the mapping
wrong: the physical index source and actual input timing remain unknown.

## Two independent input additions in q1 and q3

Both profiles decode 002 and 076 as `Q = D+Q` with mapped carry zero. From
zero reset, let A be the byte supplied at 002 and B the byte at 076:

1. Instruction 002 leaves Q=A.
2. Instruction 076 leaves Q=`(A+B) mod 256`.
3. No later instruction writes Q before the first 109.

In the independent-input experiment, the other reads use D=1 with the same
1-then-zero early replies. The first-dispatch state is therefore:

| Value | q1 | q3 |
| --- | --- | --- |
| R0 | FF | FF |
| Q | A+B | A+B |
| Current Y | Q | Q+1 |
| Previous Y | Q+2 | Q+2 |

Previous Y comes from 108: it adds its default input 1, Q, and carry 1 from
the final capture at 107. The difference in current Y arises at 109 itself:
q1 exposes Q, while q3 subtracts R0=FF from Q, giving Q+1 modulo 256.

All 65,536 A/B pairs are checked for each profile, using Q as the actual index
source. **All eight handler entries are reached**, 8,192 times each per
profile. The current/previous-Y equations also span all eight residues for
these independent inputs, though this exhaustive split-input run selects Q.
For example, A=A5 and B=5E sum to 03 after wraparound, selecting entry 3;
q1 exposes current Y=03 and q3 exposes 04 in the same incoming state.

## The selected branch table

Under the retained default unconditional policy, the eight table words branch
to these handler entries:

| Entry | Branch word | Handler entry |
| --- | --- | --- |
| 0 | 10A | 11A |
| 1 | 10B | 148 |
| 2 | 10C | 18B |
| 3 | 10D | 300 |
| 4 | 10E | 259 |
| 5 | 10F | 345 |
| 6 | 110 | 09E |
| 7 | 111 | 133 |

Each split-input prefix executes both the dispatch and the selected real
branch word; the handler is not installed as a synthetic starting PC. All
arrive with live stack depth zero. Optional BRT-gate experiments use different
transfer policies and are outside this table-entry claim.

## Validation and interpretation

The study checks **6,144 scalar prefixes** (six mappings × 256 bytes × four
sources) and **131,072 independent-input prefixes** (q1/q3 × all A/B pairs).
All start from zero reset, use real Am2901/8X02 steps, remain within the stack
limit, and reach a first handler within the 64-instruction bound. The scalar
report stores each common incoming state once, alongside all four observed
source choices. An execution digest covers the full traces and final states.

Twenty-five scalar witnesses and sixteen split-input witnesses are replayed
through the ordinary core runner. Every instruction's PC/next PC, ALU result,
test, carry input, Q, RAM delta and complete stack state matches the prefix
runner; final RAM/Q/SP/stack also agree. The split witnesses cover all eight
handler entries for each of q1 and q3 with nonzero independent inputs.

This feeds back into mapping evaluation: the scalar fixture's parity limit
cannot by itself reject Q-based q1/q3 dispatch, while q2/q4's constant
current-Y result needs a different explanation if that signal is proposed as
an input-code selector. Reaching more handlers is not evidence of correct
wiring. These results retain the alternative layouts and make their input
requirements explicit; no default mapping is promoted or changed, and no
physical command protocol is assigned.

## Reproduce

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/selector_prefix_study.py
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -p 'test_*.py'
```

[Configuration](selector-prefix-study.json), [script](selector_prefix_study.py),
and [report](results/selector-prefix-study/report.json) retain the source
choices, input schedule, equations, entry counts, full witnesses and hashes.
