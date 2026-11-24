# Handler 7: input carry selects transform calls

Under q3 with previous flags, handler 7 selects no transform, only the final
transform, or all three transforms according to an input-sum carry and a
comparison with captured R7. Full reset executions connect these choices to
retained registers and exact terminal-entry cycles. This describes
computational behavior under the declared mapping, not a recovered filter or
physical input protocol.

## Reset inputs and preparation

Input code `c=7,15,...,255` is assembled by the existing reads at 002 and 076
and selects handler 133 through Q at 109. Early PLP-side replies remain [1,0],
all later dispatch indices are two, and other external reads default to one.
D107=(x+1)&255 captures R7=x. This study independently supplies A at 137 and B
at 138.

The call at 133 enters 341–344, which repeatedly copies the nonzero Q code
into R0 under q3. 134 copies that value to R5, and 136 copies the initially zero
R3 to R2. Then:

```
R3 = (A-c-1) & 255
k  = (A > c)
t  = c + B + k
Q  = t & 255
```

The strict comparison in k comes from 137's subtraction with carry-in zero.
Its carry feeds the addition at 138. Ignoring that one-bit contribution changes
the overflow boundary; it is not equivalent to testing c+B alone.

## Three paths and timing

139 tests the inverse of the previous addition's carry. If t<256 it branches
straight to 13E. On overflow, 139 also performs the ordinary subtraction
c−x with carry-in one. 13A tests the inverse of that carry, distinguishing c<x
from c>=x.

| Condition | Calls executed | First 084 cycle |
| --- | --- | ---: |
| t<256 | None | 62 |
| t>=256 and c<x | 3C0 only | 73 |
| t>=256 and c>=x | 3EA, then 3D5, then 3C0 | 93 |

For example, c=7, A=7, B=248 takes the direct path because t=255.
Changing A to 8 adds the carry contribution and makes t=256. Captured x=7
then selects all three calls, while x=8 selects only 3C0. At c=255 no byte A
can make A>c, and no byte x can make c<x; the final-transform-only path is
therefore excluded for that code.

## Why these transform calls return

In these zero-reset fixtures R10–R13 are zero. The declared entry-two calls
reach 3F7–3FA, 3E2–3E5 and 3CD–3D0 respectively. Each pair negates a zero
16-bit source, preserving zero in its output words. The source overlap in
3F7–3FA is retained: later instructions see the R12/R13 values just written.
With zero inputs those new values are also zero.

The wrapper PLPs copy R0 into R3, R2 or R1 respectively. Their previous-zero
loop tests see the final zero table result and return after one pass. Thus:

- 3EA overwrites R3 with c.
- 3D5 overwrites R2 with c.
- 3C0 overwrites R1 with c and replaces R4–R7 with zero.

Q is preserved by all three calls. Each call costs ten instructions including
its BSR. The overflow path adds the 13A branch instruction, accounting for
11 or 31 additional instructions over the direct path. Maximum reset-stack
depth is two without these calls and three with them; all paths end at depth
zero. No stack or PC repair is used.

This one-pass result depends on the zero source words and fixed table entry.
It does not establish termination for arbitrary transform state or other
computed-call targets.

## Complete terminal state

All paths preserve R0=c and Q=t&255. RAM outside the following entries is zero:

| Path | Nonzero-capable retained registers |
| --- | --- |
| Direct | R3=(A−c−1)&255; R4=(c+1)&255; R5=c; R7=x |
| Final transform only | R1=c; R3=(A−c−1)&255 |
| All transforms | R1=R2=R3=c |

The listed registers may themselves evaluate to zero. R0=c is common to every
row and is omitted from the table. The captured x is erased whenever 3C0 runs.
The direct path preserves the input-derived R3, while the all-transform path
replaces it with the input code.

13E–147 mostly expose transient values without further RAM/Q writes. Under
the declared true selector 5, 144 skips 145; 147 takes the direct terminal entry
at 083. That entry does not execute the earlier terminal register-store
helpers, so the R1–R3 distinctions survive at 084. Alternate selector-5 behavior
at 144 is outside this reset contract.

## Evidence

The four-instruction gate checker uses actual Am2901/8X02 steps at 137–13A.
It exhausts every A/B pair for c in {7,255} and x in {0,255}: 262,144 local
arithmetic/branch comparisons. Those checks begin at a local gate state and
are not presented as additional reset runs.

The full reset sweep has 2,492 cases covering all 32 handler-7 codes, capture
values at zero, equality, immediately above the code when representable, and
255, plus input values around the carry/overflow boundaries. Each run checks
all final RAM/Q, exact first-terminal cycle, actual transform-call sequence,
entry-two dispatch, loop exits and stack depth. The observed gate ALU results
and branch targets also match the independent local checker.

Five full boundary witnesses cover the three routes for c=7 and the two
possible routes for c=255. Regression tests distinguish A=c from A=c+1,
x=c from x=c+1, and the FF wrap-to-zero Q case. These tests do not sweep every
possible captured byte or claim an exhaustive all-state transform analysis.

[Configuration](handler7-study.json), [runner](handler7_study.py), and
[report and witnesses](results/handler7-study/report.json).

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/handler7_study.py
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -p 'test_*.py'
```
