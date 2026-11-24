# Handler 1: input parity and timed terminal continuations

The alternative 178–17F continuation preserves the same final state as the
normal 180 path, but exposes different arithmetic and can add three or four
instructions. An earlier input supplies the one-bit Q value that controls a
skip at 17F. This extends the [wrapped-sum study](HANDLER1.md), whose default
input at 164 cleared that bit.

## Inputs and entry state

Use q3, previous flags, the established PLP replies and fixed later dispatch
index 2. Code c is congruent to 1 modulo 8. As before, independent bytes u at
167 and v at 16A leave R14=((u+v)&FF)>>1. Supply d independently at 164 and
w at 17F. The external-condition policy is separate from these byte reads.

At 164, Q=1, so the subtraction writes R3=(1-d)&FF. The previously studied
shift drains subsequently clear Q. 172 copies R2=1 into R15, and 173 writes
Q=R3 AND R15. Consequently **p=(1-d)&1** is the surviving Q value: p=1 for
even d and p=0 for odd d. 174 then writes R15=c+3 and 176 writes R2=p+1.
R0 is zero at 177. This is a retained parity bit under the declared decode,
not a claim about the physical role of the input channel.

Let B be the baseline first-terminal cycle from the wrapped-sum study:

```
z = ((2*c)&255) >> 2
n = 1 if z==0 else 9-trailing_zero_bits(z)
B = 195 + 2*n + 2*bit_length(u>>1)
t = B-31
```

177 executes at cycle t. Neither d nor w changes the earlier drain lengths.

## Three external-line schedules

Selector 5 is declared as a direct external line, initially high. Selector 6
and other conditions retain the original assumptions.

| Schedule | Continuation | First terminal 084 |
| --- | --- | --- |
| Stay high | 177 → 180–186 → 0E9/0EA | B |
| Fall at t and stay low | 177 → 178–17E → 0E9/0EA | B |
| Fall at t, rise at t+3 | 177 → 178–17A → 17F → 180/181–186 → 0E9/0EA | B+4-p |

All three runs have identical PC, ALU, RAM/Q and stack transitions before t.
A fall delayed to t+1 leaves the normal 180 route selected. A rise delayed to
t+4 misses the 17A test and leaves the 17B route selected. These negative
controls use scheduled line values, with no forced branch or injected state.

178 exposes D+Q without loading it. 179 copies R0=0 into R3, clearing the
earlier input difference. 17A exposes R0 OR Q=p while testing selector 5.
If the line remains low, 17B exposes R0+R14+1, 17C exposes R0-Q-1 and 17D
exposes R0+Q. 17E unconditionally joins 0E9. None changes RAM or Q.

If the line has risen, 17A takes 17F. That instruction stores
R2=((w+p)&FF)>>1, leaving Q unchanged. Its skip uses the previous zero flag
from **17A's OR**, not the sum or carry produced by its own input w:

- p=0: no skip; 180 overwrites R2 with its default input 1.
- p=1: skip 180; the temporary half remains until the terminal tail replaces it.

For example, p=1 and w=FF produces a zero half after byte wrap but still skips
180. Changing w therefore changes an intermediate register value without
changing the skip, final state or execution time. The following 181–186
sequence clears R3 and exposes arithmetic without changing Q or R14.

Both continuations execute 0E9, exposing R12-R0-1=0, followed by 0EA's
unconditional branch to 07B. 0EA exposes XNOR(R0,Q), but its result does not
select an entry at 078. These paths bypass 078–07A entirely.

## Final state

At terminal 084, Q=p and all RAM is zero except:

| Register | Value |
| --- | --- |
| R4 | c+1 |
| R5 | 127*p |
| R12 | 1 |
| R14 | ((u+v)&FF)>>1 |
| R15 | (c+3)&FF |

The terminal helpers form R0=p>>1=0, and both indexed stores target R2,
clearing its temporary input-derived values. Their other shifted result is
R5=((-p)&FF)>>1, accounting for the retained 0/127 difference. The earlier
R3 parity difference is cleared by 179 or 182. Maximum stack depth is three;
all paths reach terminal with no active frame. Timing is expressed only in
microinstructions, not physical sample periods.

## Verification and scope

A local check executes the actual 164/173/17A/17F arithmetic for all 65,536
(d,w) pairs, preserving nonzero unrelated RAM and checking the complete RAM/Q
result. It separates the previous zero flag from the current wrapped sum.

The integrated runner checks 1,536 full reset cases: every code, four u/v
pairs, four d boundaries and all three line schedules. It compares the full
entry and final state, branch paths, temporary shifted value, terminal timing
and stack balance. There are 1,024 exact state-prefix comparisons against the
high-line counterparts and twelve saved witnesses covering both parity values,
all schedules and code boundaries.

Regression tests add independent random bytes, both w extremes for each
parity, changes to w that must not affect final behavior, and one-instruction
late fall/rise controls. The witnesses replay without local state injection.
Physical input and line assignments, transient Y consumers and the modem
function remain unresolved. Other initial states or earlier input policies
are outside these contracts.

[Configuration](handler1-branches.json), [runner](handler1_branches.py),
[report and witnesses](results/handler1-branches/report.json).

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/handler1_branches.py
```
