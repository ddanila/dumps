# Outer input leaves: replacement and comparison-qualified return

*Runs under the [shared assumptions](ASSUMPTIONS.md).*

Two entries in the outer computed-call table have different retained effects.
221 loads a temporary byte, calls a difference helper, then replaces Q from a
second input. 2B3 preserves Q, clears R15 in this context, and either returns
through 227 or exposes R2 three times before returning at 2BB. The previously
unnamed 221–223 and 2B9–2BB words are exercised from actual zero reset.

## Caller and input-derived selection

Use the [alternate handler-4 preparation](HANDLER4-ALTERNATIVES.md) under q3:
previous flags, the established early replies, selector 5 initially high then
falling at cycle 70, and code c congruent to 4 modulo 8. Supply d at 25D. The
preparation preserves Q=d, sets R3=R12=c+1 and R14=(-c)&FF, and reaches 26F
at cycle 81. Global index 11 selects 217 and both eventual R11 stores.

217 calls 21A, which increments R4 to (d+2)&FF and copies zero R1 into R2.
At 21F, cycle 88, R0=FF, Q=d, R2=0 and there is one live caller frame.
Set only 21F's index source to previous Y, which equals d from 21E. The call
itself exposes zero, so current Y is a distinct alternative.

The inherited table is checked against all 82 bytes at Am27S31 offset 080,
adding bank 200 to each byte. Its association with 21F remains a hypothesis.
Reduction modulo 82 gives these complete sets of selecting byte values:

| Target | d values, hexadecimal |
| --- | --- |
| 221 | 00, 52, A4, F6 |
| 2B3 | 10, 20, 30, 40, 50, 62, 72, 82, 92, A2, B4, C4, D4, E4, F4 |

These nineteen d values are all tested. Other table targets are outside this
study. Q as the index gives the same selections in this caller state. Current
Y is zero and always selects **221**, including for the values that otherwise
select 2B3. Source controls verify the resulting change in retained Q.

## 221: temporary input, nested difference exposure, replacement input

Let u=D221 and p=D225. The sequence is:

1. 221 loads Q=u; 222 exposes zero without a retained write.
2. 223 exposes R0 XOR Q, then calls 228 with a real third return frame.
3. With R0=FF, 228/229/22A expose u, (u+1)&FF and (u-1)&FF respectively.
   They preserve RAM and Q, and 22A returns to 224.
4. 224 exposes R15-R0=1; 225 replaces Q with p.
5. 226 exposes zero, and 227 returns to 220. 220 returns to 218, the caller
   of 21A. 219 then joins the terminal path at 078.

The temporary u affects ALU outputs but has no surviving register or timing
effect in this path. Q=p is the retained result. The nested helper is neither
a fabricated return nor a stack repair: the active depths at 217, 21F and
223 are one, two and three, and each POP consumes its corresponding frame.

## 2B3: preserve Q and choose a return by comparison

2B3 copies R10 into R15, and 2B4 replaces it with R11. Both source registers
are zero here, so final R15=0. 2B5 and 2B6 expose input differences without
storing them. Their carry feedback does not decide the following branch:
2B7 uses fixed carry one to compute Q-R0, and 2B8 tests **that** carry.

For general byte operands q and a=R0, the branch to 227 is taken iff q>=a.
Otherwise 2B9, 2BA and 2BB each expose R2, preserving all RAM and Q; 2BB
then returns directly to 220. Their differing A register fields do not change
this behavior because the selected source is zero/B and B is R2 in all three.

In the present reset context a=FF and every selecting d is below FF, so 2B8
always falls through. Q=d survives, and the three Y values are all zero.
The return consumes the frame pushed by 21F; 220 consumes the outer 217 frame.
No optional branch gate is required.

This differs from the older [nested-wrapper controls](MASKED-NESTED-DISPATCH.md),
where 2BC first makes R0=Q>>1. Their inner 2B3 calls necessarily satisfy Q>=R0
and take 227. The saved controls at masks 51/A3/F5 confirm that opposite guard
outcome. A prepared-caller invariant must not be applied to the direct outer
call, which retains R0=FF.

## Complete result and timing

Let q=p on the 221 path and q=d on the 2B3 path. At terminal 084, Q=q and
the full RAM state is:

| Register | Value |
| --- | --- |
| R0, R11 | q >> 1 |
| R2 | (q+1)&FF |
| R3, R12 | c+1 |
| R4 | (d+2)&FF |
| R5 | ((-q)&FF) >> 1 |
| R14 | (-c)&FF |
| All others | 0 |

The two terminal stores target R11. R15 is zero throughout this return
context. The 221 path first executes 084 at cycle 126, or 125 when p=0 makes
078 skip 079. The 2B3 path reaches 084 at cycle 125 for every selecting d.
Maximum stack depth is three, with no active frame at terminal entry. These
are microinstruction counts; no physical sample or output timing is assigned.

## Verification and documentation correction

A local check executes the 2B7/2B8 arithmetic for all 65,536 Q/R0 pairs,
with nonzero unrelated registers and varying R2. Exactly 32,640 pairs fall
through. For each of those it checks all three Y values and full RAM/Q
preservation through 2BB. The local arithmetic does not claim arbitrary
caller-stack validity; the full reset traces verify real calls and returns.

There are 2,432 complete reset cases: 32 handler codes, all nineteen selecting
d values and four independent u/p pairs. Ten additional source controls
compare Q and current Y with the default previous Y. Eight saved witnesses
cover both paths, payload zero, nonzero temporary loads and code boundaries.
Regression tests add random inputs, perturb overwritten or unread inputs and
the transient differences at 2B5/2B6, and compare index sources. Checks include
complete retained state, intermediate outputs, ROM table bytes, call depths,
return addresses, exact timing and terminal selection.

The earlier masked-nested document incorrectly said current Y at **21F**
selected 2B3. Its saved traces and report actually select 221 and reach 084
at cycle 227. That text is corrected without changing the historical results.
Current Y at the separate **2C4** site does select 2B3 and reaches 084 at 234.

Physical dispatch wiring, temporary Y consumers and input-channel meaning
remain unresolved. These are caller-specific contracts under the explicit
q3 mapping, input schedules and table hypotheses.

[Configuration](input-leaves.json), [runner](input_leaves.py),
[report and witnesses](results/input-leaves/report.json).

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/input_leaves.py
```
