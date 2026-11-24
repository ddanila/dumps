# Handler 4: sum-carry and comparison-selected inputs

Under q3, the continuation at 2A0 selects an input value through two arithmetic
conditions. It preserves the first input when a byte sum carries; otherwise it
increments that input and either keeps the result or replaces it from later
reads. A subsequent skip uses a logical XOR carry, distinguishing captured R7
values 00 and FF. This study connects those decisions to surviving registers
and the terminal stores through actual reset execution.

## Reset context

Use input code 4 with the [handler timing](HANDLER-TIMING.md) previous-flag
scenario: 109 selects with Q, all later table indices are 2, early replies at
117/106 are `[1,0]`, and default external D is 1. At 107 supply `(x+1)&FF`
to capture R7=x; this study tests x=00 and FF.

259 calls 314, preparing R4=5. 25A calls wrapper 3A2, which copies R4–R7
into R12–R15, preserving Q=4. Its paired table entry 2 subtracts each copied
operand from itself, exposing four zero result bytes. The previous-zero loop
test returns after one pass, even when captured R7=FF. These transient results
are not identified physical output writes.

25C–264 replace Q from the default input, write R3=~R4=FA, and clear R14.
At cycle 71, execution reaches 2A0 with no active stack frame. The study
captures the real RAM, Q, flags and circular-stack slots at this boundary;
it does not construct a local entry state. Earlier writes of R13 from input
preparation have already been overwritten by the copied R5=0.

## Input selection

Supply A at 2A0 and B at 2A2, leaving every later read at 1. Let
`c=(A+1)&255`. The Q value reaching 26F is:

| Condition | Path | Selected Q |
| --- | --- | --- |
| A+B >= 256 | 2A3 takes 2B1 | A |
| A+B < 256 and c <= 1 | 2A7 takes 2AA | c |
| A+B < 256 and c > 1, x=00 | 2A8 skips 2A9 | 1 |
| A+B < 256 and c > 1, x=FF | 2A8 executes 2A9 | 2 |

The conditions come from distinct instructions:

1. 2A0 loads Q=A; 2A2 stores `(A+B)&FF` in R15. 2A3 tests that addition's
   carry and takes the short exit when it overflows. Q still contains A.
2. Otherwise, 2A4 adds default D=1 into Q. 2A6 computes `1-Q`, and 2A7
   tests its carry: no borrow means Q<=1. That path preserves Q.
3. In the fallthrough path, 2A8 reloads Q=1 but tests the flag from 2A7's
   XOR. With R0=FF and mapped carry-in zero, that XOR's carry is one iff
   R7 is not FF. Thus x=00 skips the additional increment at 2A9, while
   x=FF executes it. This skip is not testing the Q reload at 2A8.

The overflowing and non-overflowing paths rejoin at 26A. 26F retains its
scenario-selected entry 2, reaching the 2C6–2CA difference-only tail and
then 0FB/0FC. Those instructions expose differences without replacing Q.
The terminal helper stores `Q>>1` twice into register 2.

## Complete retained state and timing

R15 retains `(A+B)&FF`. R14 is zero on the sum-carry exit and one otherwise.
At terminal 084, the full RAM state is:

| Register | Value |
| --- | --- |
| R0, R2 | Q>>1 |
| R3 | FA |
| R4 | `(Q+1)&FF` |
| R5 | `((-Q)&FF)>>1` |
| R7 | x |
| R12 | 5 |
| R14 | 0 for sum carry, otherwise 1 |
| R15 | `(A+B)&FF` |
| All others | 0 |

Q itself survives. For A=FF, B=00, Q becomes zero through the increment and
comparison path. Changing B to 01 instead takes the sum-carry exit and leaves
Q=FF, so the terminal stores contain 7F. For A=01, B=00, changing captured
R7 from 00 to FF changes final Q from 1 to 2, and the stored half from 0 to 1.

From the cycle-71 checkpoint, reaching 26F takes 11 instructions on sum carry,
20 on comparison, or 21/22 on reload with x=00/FF. First execution of 084 is
32 instructions after 26F, except Q=0 skips one instruction. The complete
reset paths therefore first reach 084 at cycles 114, 122, 123, 124 or 125.
These are microinstruction counts, not sample rates.

## Validation and scope

Both x values have freshly replayed zero-reset checkpoints. All 65,536 A/B
pairs are checked from each checkpoint: 131,072 actual ALU/sequencer
continuations. Each is compared against the entire predicted RAM/Q state,
path and instruction count. Per captured value, the partition is 32,640
sum-carry paths, 257 comparison paths and 32,639 reload paths.

There are also 2,560 complete 160-instruction reset runs: every A, both x
values and B in {00,01,7F,80,FF}. Every restored continuation step must match
the main runner; final RAM/Q, stack balance and terminal recurrence are also
checked. Ten full witnesses cover each branch and the FF increment boundary.

The result is scoped to q3, previous flags, the defined logical-carry model,
input code 4 and the stated default reads/dispatch. Other captured values,
input sites and dispatch sources are not swept here. The alternate 265–269
continuation is excluded by the selected constant condition. No physical
protocol or modem algorithm is assigned to the value selection.

[Configuration](handler4-study.json), [runner](handler4_study.py),
[report and witnesses](results/handler4-study/report.json).

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/handler4_study.py
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -p 'test_*.py'
```
