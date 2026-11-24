# Handler 6: early complement diversion and conditional input addition

Raising the declared selector-1 line at 0C0 or 0C1 reaches 0E0–0E4 before the
late continuations already studied. This changes Q from zero to FF. The same
later capture at 0E5 consequently becomes input-minus-one, and the branch at
0CE usually skips the following input addition. Reusing the late-entry formulas without
accounting for this earlier state would give the wrong answer.

The configuration retains q3, previous flags, zero reset, matched PLP replies
and table index two. Selector 1 is an initially low scheduled external line,
raised at an absolute cycle predicted before execution. This is an explicit
condition-source hypothesis, not recovered wiring or a PC-specific override.

## Entry and temporary operations

Let B be the baseline handler-6 first-terminal cycle from [HANDLER6.md](HANDLER6.md).
Raise the line at B-37 to branch from 0C0, or B-36 to branch from 0C1 after
0C0's ordinary fallthrough. Every earlier PC, next PC, ALU result, RAM write,
Q value and stack state is checked against the unchanged baseline.

Both entries reach 0E0 with R0=Q=0. 0E0 exposes an input sum without a retained
write. 0E1 computes Q=~R0 with carry zero, giving FF. 0E2 writes an input mask
into R5, and 0E3 writes a second masked input into R0. 0E4 branches to 0C4.
These two captured values are temporary: 0C6 overwrites R0 and 0E5 overwrites
R5 before either can affect the retained state described below.

The original masked/halved result remains R13=t and R15=h, where:

```
m0 = captured_byte & (code+1)
t = (m0 + int(m0!=0)) & 255
h = t >> 1
```

## Why the later capture changes sign

Define d=D0C6 and a=D0E5. Since Q=FF, 0C6 writes R0=d and produces logical
carry according to that mask. Under the declared logical-flag model, the
following XNOR at 0C7 produces carry zero for every d. Selector 1 is now high,
so it takes 0E5, whose addition is a+FF+0:

```
s = (a-1)&255
R5 = s
```

The later-only entry studied in [HANDLER6-LATE.md](HANDLER6-LATE.md) instead
had Q=0 and carry one at this point, producing a+1. Both are checked contexts;
neither formula is global to the helper address. 0E6/0E7 make temporary writes,
and 0E8 rejoins 0C8. The existing copies restore R12=h before 0CB.

## The conditional addition after 0CE

At 0CB, Q is still FF and R0=d. Its ~R0 AND Q operation produces carry one
exactly when d is not FF. The taken selector-1 branch enters 0CE, which copies
d into Q while testing that previous carry:

- d!=FF: TSK skips 0CF. Q remains d; D0CF is not read there.
- d=FF: TSK allows 0CF. It adds u=D0CF to the existing FF, giving Q=(u-1)&255.

If v=D0D4, the effective mask is therefore m=v AND (((u-1)&255) if d=FF else d).
The decoded operations at 0C6, 0C7, 0E5 and 0CB are checked for all 65,536
d/a pairs. In particular, the addition boundary is equality with FF, not a
sign-bit test or an arbitrary large-input threshold.

## Retained result and timing

The remaining continuation is the already checked 0CE path: 0D2 copies R5=s
into R3, 0D4 stores m in R0, and the 04C helper clears Q and copies s into R12.
The zero flag from m AND s selects the normal exit to 079 or the alternative
0DF/1D3 tail. The complete final state is:

- Q=0; R7 retains the original captured byte; R13=t; R15=h; R12=s.
- If m AND s is zero: R3=s and R4=2.
- Otherwise: R3=0 and R4=m.
- All other RAM registers are zero.

Let e=1 for the 0C1 entry and zero for 0C0, r=int(d==FF), and
A=int((m&s)!=0). The first terminal cycle is:

```
B + 28 + e - (1-r) + 8*A + int(A==0 and m==(h^255))
```

The last term is the previously established extra 07A instruction on the
normal exit. Skipping 0CF saves one instruction. Entering through 0C1 costs
one more than 0C0. Maximum stack depth is two and final depth zero. No terminal
arrival is identified as a physical completion signal.

## Evidence and scope

The study runs 2,304 complete 192-instruction reset cases: all 32 handler codes,
both entry points, four d boundaries, three a boundaries and three u/v pairs.
The selected original capture is zero for code 06 and FF for the others;
randomized regressions vary it and all later inputs independently. Those tests
also perturb the discarded 0E2/0E3 reads and vary u when 0CF is skipped.

Each run checks the unchanged prefix, actual entry targets, the Q complement,
capture carry, addition/skip, masked value, exit choice, complete final RAM/Q,
terminal cycle and stack depths. Eight saved reset witnesses cover both entry
points and both sides of the addition boundary at small/large codes. Every
newly annotated address appears in these witnesses and replays byte for byte.

This completes the meaning of 0E0–0E4 for the declared reset continuations;
it does not assign the same contract to arbitrary state or to 0E9 onward.

[Configuration](handler6-early.json), [runner](handler6_early.py), and
[report](results/handler6-early/report.json).

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/handler6_early.py
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -p 'test_*.py'
```
