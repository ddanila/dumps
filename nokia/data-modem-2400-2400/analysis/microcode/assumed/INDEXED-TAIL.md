# Two indexed register stores in the terminal tail

*Runs under the [shared assumptions](ASSUMPTIONS.md).*

Under q2, the two computed calls at 07E and 081 select destinations in the
register file. Their sixteen one-word entries at 08A–099 copy R0 into R0–R15
respectively, then return. The preceding helper prepares R0=`Q>>1`, so the
terminal tail performs two indexed stores of the same shifted Q value.

This connects the [nested input load](NESTED-RESET.md) and subsequent
[save/load helper](AFFINE-TAIL.md) to concrete RAM writes. The table address
source remains hypothetical. A possible simultaneous external capture of Y
is not established by these RAM effects.

## The five-instruction preparation helper

Under the selected zero-fill shift and carry policies, each call to 085–089
has these effects:

| Address | Effect |
| --- | --- |
| 085 | R0 = 0 |
| 086 | R5 = `((D−Q−1) mod 256) >> 1` |
| 087 | R0 = Q >> 1 |
| 088 | R0 = Q >> 1 again |
| 089 | Expose `(D−R6) mod 256` on Y; return |

Q is preserved throughout. The shifts affect RAM, not Q, so the second call
prepares the same half-Q value. The arithmetic at 086 wraps to a byte before
shifting; it is not a nine-bit subtraction followed by a shift. Constant D
within a fixture gives the same R5 preparation on both calls.

07C and 07E copy R1 into R2 before the first indexed store. The first table
entry may then overwrite any selected register. The second helper rewrites
R0 and R5 before the second indexed store, so some first-store effects can be
lost. For example, a first store into R5 is overwritten by instruction 086
on the second helper call unless the second store also targets R5.

## Candidate index values

Indices are reduced modulo the declared sixteen-entry table:

| Candidate | At 07E | At 081 |
| --- | --- | --- |
| Scenario | Declared index | Declared index |
| Current Y | R1 before the first store | 0 |
| Q | Q | Q |
| Previous Y | D−R6 before the first store | D−R6 after the first store |

The R1 value at 07E comes from that call instruction's own copy into R2.
At 081 the ALU computes zero AND Q. Previous Y instead comes from the
immediately preceding return at 089, where the helper calculates D−R6.

If previous-Y indexing makes the first store target R6, the stored half-Q
value changes the calculation of the second address. With Q=00, D=07 and
initial R6=41, the first index is C6 (entry 6), storing zero in R6. The second
index becomes 07 (entry 7), storing zero in R7. With Q=02 in the same fixture,
the full second index becomes 06: the computed byte changes, but both table
entries are 6 after reduction. This distinction matters when comparing full
index values with selected targets.

## Exhaustive Q/input sweep under explicit fixtures

The local experiment begins at 07C with an empty stack and explicit RAM/Q
fixtures. It executes the real four calls and returns through 083, stopping
at 084. It checks all 65,536 Q/D pairs for each of four index sources:
**262,144 clean local tails**.

R1 is initialized to `D XOR A5`, R6 to `(2*D+33) mod 256`, and the other
registers to fixed nonzero values. These choices exercise every first table
entry for each candidate and the feedback case where the first destination
is R6. They are declared slices of the initial-state space, not exhaustive
combinations of Q, D and all sixteen registers. The local scenario candidate
uses D as the fixed index at both calls; the reset comparisons below retain
independent seeded choices.

| Source | Local tails | First destination R6 | Different first/second destinations |
| --- | --- | --- | --- |
| Scenario | 65,536 | 4,096 | 0 |
| Current Y | 65,536 | 4,096 | 61,440 |
| Q | 65,536 | 4,096 | 0 |
| Previous Y | 65,536 | 4,096 | 3,840 |

Every run matches an independent full-RAM prediction, preserves Q, uses
maximum stack depth one and returns to depth zero. The complete sequence
from 07C to first entry at 084 is **20 modeled instruction cycles**. The two
table stores occur at local cycles 8 and 17, nine cycles apart. These are
relative microinstruction counts; no physical clock rate, sample rate or baud
rate is inferred. Twelve complete integrated witnesses check instruction
addresses, ALU results, tests and next addresses against the local runner.

## Matched reset comparisons

All five nested q2 reset cases are replayed with each source at both terminal
calls: twenty clean runs. For each seed, the trace before the first terminal
computed call is identical across sources. The original scenario-source
trace digests also match the earlier reset study. No random dispatch follows
these last two calls, so unlike the earlier nested-call experiment there is
no later random choice to confound the comparison.

The same half-Q byte is stored twice in each run:

| Seed | Q | Stored byte | Scenario-selected registers | Current-Y registers | Q-selected registers | Previous-Y registers |
| --- | --- | --- | --- | --- | --- | --- |
| 115 | CC | 66 | R10, R15 | R0, R0 | R12, R12 | R1, R1 |
| 501 | DE | 6F | R10, R11 | R0, R0 | R14, R14 | R1, R1 |
| 2855 | 20 | 10 | R14, R15 | R0, R0 | R0, R0 | R1, R1 |
| 3519 | 00 | 00 | R13, R0 | R0, R0 | R0, R0 | R1, R1 |
| 3614 | 8F | 47 | R1, R6 | R0, R0 | R15, R15 | R1, R1 |

All candidates reach 084 at the same cycle for a given seed, but their final
RAM states differ. For example, seed 115's original second store overwrites
the affine R15 result CD with 66. The three datapath candidates leave CD in
R15 and store 66 elsewhere. Thus terminating cleanly does not select one
candidate as the physical index source.

In these five reset fixtures, R1 initially equals zero and R6 equals D−1.
That explains the current-Y first entry 0 and both preceding-Y entries 1.
The local R6-feedback case is not demonstrated by these five reset states.
No global reset-reachability or physical output claim is made for that case.

## Reproduce

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/indexed_tail_study.py
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -p 'test_*.py'
```

[Configuration](indexed-tail-study.json), [script](indexed_tail_study.py), and
[report](results/indexed-tail-study/report.json) retain the fixture scope,
execution digest, twelve local witnesses, twenty full reset comparisons and
source hashes. The new arithmetic/store annotations apply only to q2.

The follow-up [diagnostic input contract](REGISTER-CONTRACT.md) supplies
independent Q and address bytes from the same verified reset prefix. It
checks all destination pairs, including R6 address feedback and the R5
overwrite, without treating the constructed inputs as a recovered protocol.
