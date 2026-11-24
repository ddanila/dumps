# Handler 4: alternate preparation and two additive continuations

*Runs under the [shared assumptions](ASSUMPTIONS.md).*

The 230 continuation adds two independently supplied bytes to Q, clears R15,
and exposes differences before the terminal stores. The 280 continuation
stores the selected value directly. An earlier external-condition change
selects 265–269, preserving a different input in Q and replacing R3/R14.
These paths complement the [bank-200 study](HANDLER4-BANK.md) and connect the
previously unnamed 0EB–0F8 block to complete reset execution.

## Scenario and preparation

Use q3, previous flags, input code c congruent to 4 modulo 8, and the
established PLP replies from [handler timing](HANDLER-TIMING.md). Global index
i is 3, 4, 5 or 6: it selects the initial paired row, the 26F branch and both
terminal register destinations. Supply independent external bytes d at 25D,
u at 235 and v at 0ED. Other reads retain their defaults.

Selector 5 is an explicitly declared direct external line, initially high.
Keeping it high takes 264 → 2A0. Falling at cycle 70 instead makes 264 fall
through to 265. Paired reset runs have identical PC, ALU, RAM/Q and stack
transitions before cycle 70. A fall at cycle 71 is too late to select 265;
negative controls retain the normal path. No branch override is used.

Before this choice, 25C has stored c+1 in R2 and 25D has loaded Q=d; that
load has no carry contribution because c+1 never overflows for these codes.
The alternate preparation is:

| Address | Operation and effect |
| --- | --- |
| 265 | Copy R2=c+1 to R3 |
| 266 | Store R3-1=c in R14, with carry one |
| 267 | Store R1-R14-1+carry=(-c)&FF in R14 |
| 268 | Expose R2+R14: low byte 1 and carry one |
| 269 | Expose Q=d, clearing that carry |
| 26A | Store d+1 in R4 using the carry from 269, not 268 |

The normal 2A0 path replaces d using the existing default selection inputs,
leaving Q=1, R3=(-c-2)&FF, R4=2, R14=1 and R15=2. The alternate path leaves
Q=d, R3=c+1, R4=(d+1)&FF, R14=(-c)&FF and R15=0. Both reach 26F with R0=FF,
R12=c+1 and all other registers zero. The active stack is empty. Entry is at
cycle 92 normally and 81 on the alternate path.

## Continuations

Indices 4 and 5 select 280, which exposes XNOR(R0,Q)=Q and branches to 078.
There is no further payload load or arithmetic accumulation before storage.

Indices 3 and 6 select 230. Let q be the Q value entering 26F (1 normally,
d on the alternate path). 230–234 expose R5-R0, Q and Q-1 without changing
retained state. 235 stores Q=(q+u)&FF; 236 exposes zero, and 237 goes to 251.
251 preserves R0. 252 exposes an external sum, 253 writes R3=FF, and 254
exposes R0. 255 unconditionally enters 0EB under the existing BRT policy.

0EB copies R0=FF into R15; 0EC immediately replaces it with R1=0. 0ED adds
v into Q, giving **p=(q+u+v)&FF**. 0EE/0EF expose R0 AND R15 and R0+R15+1.
0F0/0F3 expose input differences; 0F1 exposes zero. Selector 6 remains false,
so both 0F2 and 0F5 fall through. 0F4/0F6 expose Q-R0-1 and Q-R0;
0F7/0F8 expose R15-R0. None of these operations changes RAM or Q.
0F9 goes to 28B, which copies R0=FF into R3, replacing 253's same value.
28C exposes R0+R5 and 28D branches to 078 while exposing XNOR(FF,p)=p.

Thus the retained effect of this longer continuation is two wrapped input
additions, R15=0 and R3=FF. Its transient Y sequence and timing are different
from the direct continuation; no external consumer is assigned to those Y
values. Other selector-6 settings are outside this study.

## Final state and timing

Let q=d for alternate preparation, otherwise q=1. Let p=q for indices 4/5,
and p=(q+u+v)&FF for indices 3/6. Before applying the final destination
overwrite, the complete terminal state is:

| Register | Value |
| --- | --- |
| R0 | p >> 1 |
| R2 | (p+1)&FF |
| R3 | FF for indices 3/6; otherwise c+1 on alternate preparation or (-c-2)&FF normally |
| R4 | (q+1)&FF |
| R5 | ((-p)&FF) >> 1 |
| R12 | c+1 |
| R14 | (-c)&FF on alternate preparation, otherwise 1 |
| R15 | 0 on alternate preparation or indices 3/6, otherwise 2 |
| All others | 0 |

Both terminal stores set **Ri=p>>1**, overriding the corresponding value in
the table. For i=3 this replaces R3=FF; i=4 replaces the prepared R4; i=5
replaces R5, including after the second helper temporarily recalculates it;
i=6 writes previously zero R6. Q remains p.

At 078, p=0 causes a skip of 079. First execution of terminal 084 is cycle
148 for the additive route or 118 for the direct route, minus 11 for alternate
preparation and minus one for p=0. Stack depth peaks at three in the initial
paired wrapper and is zero at terminal entry. These are microinstruction
counts, not a recovered sample rate.

## Validation and limits

The runner checks 2,048 full reset executions: 32 codes, four indices, eight
(d,u,v) tuples and both preparation paths. The tuples exercise zero, FF,
wrapped sums and boundaries on both paths. All 1,024 pairs match before the
external transition. Eight saved witnesses cover all four indices, both
preparations, zero-payload skips and input wrap.

Regression tests add independent random inputs, perturb the transient-only
reads at 252/0F0/0F3, and move the external fall one instruction too late.
Checks compare the complete entry and final RAM/Q, exact branch sequence,
intermediate arithmetic, terminal timing and stack balance. Saved witnesses
replay without state injection. The raw ROMs and execution model are unchanged.

These contracts are scoped to the documented input and table policies. They
do not establish the physical source of selector 5, an input protocol, the
meaning of transient output values or a modem signal-processing algorithm.
0E9/0EA and alternative selector-6 exits are not covered by these reset paths.

[Configuration](handler4-alternatives.json), [runner](handler4_alternatives.py),
[report and witnesses](results/handler4-alternatives/report.json).

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/handler4_alternatives.py
```
