# The complete q3 carry-gated input helper at 366

*Runs under the [shared assumptions](ASSUMPTIONS.md).*

366–36F prepares three registers, runs the carry-controlled three-add loop,
and on return masks an external byte with Q into R0. Reading the whole call
reveals that the preparation values do not survive the first loop iteration,
and that the return instruction changes the R0 preserved inside the loop.

This study uses q3, previous carry at the BLT, mapped/previous carry input,
and a declared constant selector 5. Local runs begin at the real BSR at 351
with an empty stack. A separate unchanged ROM-read reset trace validates a
complete call in its real context. None of these assumptions is promoted to
recovered board wiring.

## Preparation and retained result

Let `a=old R0`, `q=old Q`, and `Dxxx` denote the byte read at that instruction.
366 writes `(D366+q)&255` to R2; 367 writes `(D367+q)&255` to R1. 368 exposes
R0 and 369 copies R0 to R3. 36A skips 36B when selector 5 is true; otherwise
36B overwrites R1 with `(D36B+q)&255`. Q is preserved throughout.

For one loop iteration define:

```
s  = a + D36C
r1 = s & 255
c  = (s >= 256)
t  = r1 + D36D + c
r2 = t & 255
r3 = (r2 + D36E) & 255
```

The three instructions store r1, r2 and r3 in R1–R3. Their Y outputs are
**a, r1, r2**, respectively: destination mode exposes the A-register value
rather than the newly calculated result. The final addition's overflow is
not the loop decision; the previous carry from t controls the BLT at 36E.

If t<256, execution reaches 36F and returns with:

- R0 = D36F AND q.
- R1=r1, R2=r2, R3=r3.
- Q and R4–R15 preserved.

Thus every preparatory write to R1–R3 is overwritten, while its transient Y
value remains visible in the trace. The return's Q mask is a genuine retained
state change, not an inferred output strobe.

## Constant local inputs: return or persistent wait

When every per-PC input is held constant, a and Q remain unchanged inside the
loop. Consequently s and t are identical on every iteration. If t<256 the
helper returns after its first iteration. If t>=256 it cannot return without
changing the inputs or assumptions.

The local executor verifies the repeated state at 36C, including RAM, Q,
previous ALU flags/Y, carry feedback, PC, stack pointer, depth and all stack
slots. The repeating computation has period three. Every read schedule has a
single held byte, so advancing a read counter cannot change a future value.
This is an exact recurrence argument, not a timeout classification.

The caller frame remains on the stack while each PLP/BLT pair pushes and pops
the loop frame. Maximum depth is two. A returning call ends at 352 with depth
zero; a repeating call retains depth one at the loop header. No stack repair
is used.

| Selector 5 | Returning helper instructions | Including caller |
| --- | --- | --- |
| true, skips 36B | 9 | 10 |
| false, executes 36B | 10 | 11 |

The repeating witnesses execute two complete loop iterations to verify equal
headers. Their checked prefixes, including the caller, contain 12 or 13
instructions respectively; those bounds are not claims that the wait ends.

## Exhaustive planes and independent inputs

The study checks 262,144 local calls, with every byte pair in each of the
following planes under both selector-5 settings:

| Plane | Varied independently | Fixed | Returns per selector | Repeats per selector |
| --- | --- | --- | ---: | ---: |
| `r0_c` | R0 and D36C | D36D=127 decimal | 32,897 | 32,639 |
| `c_d` | D36C and D36D | R0=255 decimal | 32,641 | 32,895 |

Q and the other external inputs follow explicit a/b formulas in the runner;
other RAM uses a nonzero fixture. These are complete two-byte planes, not an
exhaustive sweep of every register and input combination. All cases check
complete retained RAM/Q, every helper PC and Y, instruction count, return or
recurrence outcome, and recurrence period against separate formulas.

Twenty saved boundary witnesses compare every trace field with the ordinary
executor. A regression test adds 96 independently randomized register/input
calls with both selector settings, breaking the correlations in the planes
and checking both return and repeat behavior.

## Actual reset call and ROM-feedback boundary

The existing `rom-carry-replies/reply-00` run reproduces all five saved files
byte for byte. It enters 366 at cycle 79 with R0=FF and Q=FF, skips 36B, reads
zero from the ROM at 36C, reads reply zero at 36D, then reads one at 36E and
36F. It returns at cycle 87 with:

```
R0=01, R1=FF, R2=FF, R3=00, Q=FF
```

The full nine-instruction helper Y sequence is `00,00,FF,FF,00,FF,FF,FF,01`.
The saved reset continues normally after this actual call; it is not a local
stack fixture presented as reset coverage.

The constant-input recurrence above must not be applied to the changing
ROM-address policy in general. [ROM-CARRY-REPLIES.md](ROM-CARRY-REPLIES.md)
already derives that feedback recurrence: with R0=FF it has both eventual
returns and multi-iteration cycles. The zero-reply reset used here returns in
one iteration, so its observed reads satisfy the local formulas directly.
No physical acknowledgement protocol, sample frequency or output destination
is assigned by either experiment.

[Configuration](carry-helper-study.json), [runner](carry_helper_study.py),
and [report and traces](results/carry-helper-study/report.json).

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/carry_helper_study.py
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -p 'test_*.py'
```
