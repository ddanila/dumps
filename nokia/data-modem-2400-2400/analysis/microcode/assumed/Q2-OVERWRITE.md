# q2 transform wrappers can alternate their own source values

*Runs under the [shared assumptions](ASSUMPTIONS.md).*

The wrappers at 3D5 and 3EA overwrite source registers, unlike the
[fixed-source wrapper at 3C0](Q2-TRANSFORM-LOOP.md). Under q2 with a constant
dispatch index and previous-zero loop control, this can produce a second-pass
return or an exact two-iteration cycle. The [study](q2_overwrite_study.py)
checks those recurrences and then follows the complete three-call path from
[handler 133](Q2-ACCUMULATOR.md).

All words below are 16-bit, with arithmetic modulo 65536 and hexadecimal
ranges. X denotes R10/R11 and Y denotes R12/R13, low byte first. Each loop
continues while its last table instruction's result high byte is nonzero.

## 3D5: the second output becomes the next X

Each iteration copies R0 to R2 and writes (A,B) to R8/R9 and R10/R11. Y and
Q remain unchanged. Because B overwrites X, the next iteration uses B as X.

| Entry | A | B and next X | Behavior |
| --- | --- | --- | --- |
| 0 | X | Y | Return if Y is 0000–00FF; otherwise settle into an eight-instruction cycle |
| 1 | −Y | X | Return if X is 0000–00FF; otherwise an eight-instruction cycle |
| 2 | −X | −Y | Return if Y is 0000 or FF01–FFFF; otherwise settle into an eight-instruction cycle |
| 3 | Y | −X | Negate X on every iteration; see below |

Entry 3 returns after one iteration for X=0000 or FF01–FFFF. For X=0001–00FF,
the first negation gives a nonzero high byte, but the second restores the
original small positive value and returns. All other X values alternate
indefinitely: period 16 instructions, except X=8000, whose negation is itself
and gives period 8. Counting the actual call at 13C through the wrapper's
return, one iteration takes 10 instructions and two take 18.

Across all 65,536 X values for entry 3, there are 256 first-pass returns,
255 second-pass returns, 65,024 period-16 cases and one period-8 case.
This distinguishes an actual second-pass success from repeatedly writing a
fixed result.

## 3EA: sequential writes change the apparent transform

Each iteration copies R0 to R3 and writes (A,B) to R12/R13 and R14/R15. X
remains unchanged; A becomes the next Y. The table's source/destination overlap
means the correct transforms are:

| Entry | A and next Y | B | Behavior |
| --- | --- | --- | --- |
| 0 | X | X | Return if X is 0000–00FF; otherwise settle into period 8 |
| 1 | −Y | X | Return if X is 0000–00FF; otherwise Y alternates |
| 2 | −X | X | Return if X is 0000–00FF; otherwise settle into period 8 |
| 3 | Y | −X | Return if X is 0000 or FF01–FFFF; otherwise period 8 |

In entry 0, the second pair reads Y after the first pair has overwritten it
with X. In entry 2, it negates the just-written −X, producing X. Treating
these instructions as an independent quarter turn would give incorrect results.

For non-returning entry 1 cases, Y=0000 and Y=8000 are fixed under negation
and produce period 8; other Y values produce period 16. No entry can acquire
a passing condition on a later iteration: its test depends only on unchanged
X or −X. Q is preserved throughout both wrappers.

## Composing the actual caller

Four hundred integrated cases start at 133 with Q=1, R7=0 and D=FF. These
are explicit local fixtures, not reset-reachable states. The accumulator
addition carries, old Q>=R7 selects 13B, and the code calls 3EA, 3D5 and 3C0
in order when their loops return. Each run uses one constant index for all
three table calls and one of 100 boundary X/Y pairs.

For indices 0, 1 and 2, the whole sequence reaches terminal 084 exactly when
the original X is 0000–00FF. For index 3, only X=0000 completes. An original
X in FF01–FFFF passes 3EA, then 3D5 negates it into a small positive X and
returns. The final 3C0 negates that value back into a high-byte-nonzero result
and repeats. Thus success in the first two wrappers does not establish success
of the three-call sequence.

In the declared boundary grid, **100 runs reach 084, 280 remain in 3EA, and
20 reach but remain in 3C0**. Every completed loop iteration is checked against
the composed full-RAM reference, including the prefix's register writes and
Q=0. Terminating runs also match the complete final RAM and Q. No synthetic
return or forced loop exit is used. This extends the earlier
[caller-chain study](CALLER-CHAIN.md), whose branches and single iterations
were explicitly supplied by its scenario, with real arithmetic flag control
under this particular retained mapping.

## Validation and limitations

The local checker covers **526,688 cases**: all 65,536 values of the controlling
word for each entry of each wrapper, plus 2,400 combinations of boundary pairs
and Q fixtures. The other source word in the exhaustive sweep follows a declared
deterministic formula; this is not an exhaustive sweep of all 2^32 X/Y pairs.
Each completed iteration's entire RAM and Q is checked against the independent
word-arithmetic recurrence. Repetition requires equal complete sequencer and
datapath states, including stack contents and previous flags, not a timeout.

Nineteen local integrated witnesses cover every distinct return count or
repeat period, and their instruction PCs, ALU results and branch tests match
the component probe. Sixteen complete caller traces retain representative
successes and failures. The report records all 400 caller outcomes and their
full-RAM checkpoints.

Constant dispatch, q2 source fields, previous-zero conditions and external D
remain assumptions. These results constrain that combination; they do not
identify physical output consumers, prove a useful modem operation, or show
that reset can reach the nonzero fixtures. Defaults are unchanged.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/q2_overwrite_study.py
```

[Configuration](q2-overwrite-study.json) and
[report](results/q2-overwrite-study/report.json) retain fixture definitions,
counts, comparison digest, source hashes and trace hashes.
