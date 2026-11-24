# A diagnostic input contract for two register stores

Under q2 and preceding-Y indexing at 07E/081, three future input bytes can
control the nested Q load and both terminal store addresses. The model can
select every destination pair and store `Q>>1` there, subject to a subsequent
overwrite when the first destination is R5.

This is a constructed, reproducible input contract using PC-keyed stubs. It
is not a recovered controller command, board protocol or physical dispatch
assignment. It combines the verified [nested reset path](NESTED-RESET.md),
[save/load helper](AFFINE-TAIL.md), and [indexed terminal tail](INDEXED-TAIL.md).

## Inputs and effects

Keep seed 115, its zero initial RAM/Q, early wait replies, and default D=CC.
Change only these future inputs and the two terminal index-source choices:

| Site | Input or policy |
| --- | --- |
| 225 | Input byte `u`, loaded into Q |
| 07E, 081 | Index source = previous Y |
| First read at 089 | `(initial R6 + first destination) mod 256` |
| Second read at 089 | `(current R6 + second destination) mod 256` |

Destinations are register numbers 0–15. The common reset prefix establishes
initial R6=CB. Let `v=u>>1`. If the first destination is R6, current R6 for the
second address is v; otherwise it remains CB. At 089, the ALU subtracts R6
from the supplied byte, so the resulting previous-Y index is exactly the
requested destination.

The two stores both write v, which ranges from 00 to 7F under zero-fill
shifting. Q retains the complete byte u; only the values written by these
two table entries are halved. The operation also has the already documented
helper effects: R0 becomes v, R2 copies the prior R1, R3 saves the prior R0,
R15 initially becomes u+1, and each shift helper writes
`h=((CC−u−1) mod 256)>>1` to R5. Selected destinations may overwrite these
intermediate or retained values. The verifier checks the full final RAM,
not just the requested destinations.

A first store into R5 is always overwritten by the second preparation call.
If the second store also targets R5, it restores v. Otherwise R5 finishes
with h, which differs from v for every u in this fixed-D contract. Thus the
first requested value is absent at completion in **3,840 of 65,536 cases**:
256 input bytes × first destination R5 × fifteen other second destinations.
Both store instructions still select their requested addresses in those cases.

## Why the second address must use the updated R6

With u=01, first destination 6 and second destination 7, the correct 089
inputs are D1 and 07:

1. D1−CB = 06, selecting R6 and storing v=00 there.
2. 07−00 = 07, selecting R7 and storing 00 there.

If the second byte incorrectly uses the old base, it is CB+07=D2. After the
first store, the ALU computes D2−00=D2, which selects register 2 modulo 16,
not register 7. The complete reset replay reproduces this wrong-address case
without any model error; clean execution does not imply the intended store.

Across the 4,096 cases where the first destination is R6, retaining the old
base selects the wrong second register in **3,840 cases**. The other 256 have
the same low four index bits by coincidence. This count is distinct from the
R5 final-value loss above, despite having the same numerical value.

Other saved examples include u=FF with destinations R6/R15, which uses 089
inputs D1/8E and finishes with 7F in both registers; and u=02 with destinations
R5/R0, where the first stored 01 is replaced by helper result 64 in R5.

## A shared reset prefix, not fabricated caller state

The experiment freshly executes the first 186 instructions from zero reset.
It stops just before the first 225 at cycle 186 and compares every prefix
trace record with the earlier seed-115 witness. The exact captured state
includes RAM, Q, PC, stack pointer, all four stack slots, live depth, previous
ALU flags/Y and previous carry.

None of the four changed sites—225, 089, 07E or 081—occurs in that prefix.
Consequently every member of the input contract has the same incoming state.
The live return addresses, from top to bottom, are 2C5, 220, 2FF and 213.
They come from actual calls in the replayed prefix; no new frame is invented
or repaired.

The exhaustive runner restores this captured state for each input/destination
combination and continues with the real Am2901 and 8X02 models. All later
computed calls use the declared previous-Y source, all condition sources are
flags or fixed stubs, and the two new input cursors have not been visited yet.
The runner rejects an unexpected computed transfer or another sequence-input
cursor rather than silently approximating it. A regression check corrupting
the top captured frame raises the model's normal unknown-stack error.

## Validation and limits

| Check | Result |
| --- | --- |
| Contract continuations | 65,536: all 256 u values × all 16×16 destination pairs |
| Correct requested store indices | Both indices in every contract continuation |
| Complete final RAM/Q prediction | Matches in every continuation |
| Stored-value range | All 128 bytes 00–7F |
| Maximum live stack depth | Four, inherited from the real prefix |
| Suffix length | 42 instructions, reaching 084 at total cycle 228 |
| Final live stack depth | Zero |
| Unadjusted-R6 comparisons | 4,096; 3,840 wrong second addresses |
| Complete 512-cycle core replays | Eight contract witnesses plus one unadjusted witness |

The 65,536 cases are continuations of a verified common prefix, not 65,536
separate full calls to the core reset runner. The nine complete core replays
check the prefix and every suffix step: PC/next PC, ALU results, conditions,
carry input, RAM deltas, Q, full stack state, dispatch input and external byte.
Their final RAM, Q, stack slots and stack pointer also match after the
remaining cycles at 084. This checks the checkpoint restoration against the
ordinary execution path, including nonzero input, changed destinations and
the intentionally wrong address.

The contract gives a concrete example of how external input bytes could
supply data and register indices under this mapping. It does not determine
which board supplies them, whether the real board indexes from previous Y,
or whether any transient Y values are also captured externally. The full
plan's physical I/O interpretation remains open.

## Reproduce

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/register_contract_study.py
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -p 'test_*.py'
```

[Configuration](register-contract-study.json), [script](register_contract_study.py),
and [report](results/register-contract-study/report.json) preserve the contract,
actual prefix checkpoint, exhaustive digest, counts, source hashes and full
witnesses. Original mappings, scenarios and raw dumps remain unchanged.
