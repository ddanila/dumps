# Handler 6: late capture, masked input and two terminal entries

*Runs under the [shared assumptions](ASSUMPTIONS.md).*

A timed selector-1 transition reaches the previously bypassed 0CE continuation.
An earlier transition also takes 0C7 through the input capture at 0E5–0E8.
The new captured value and a masked input determine whether 0DE enters the
normal terminal path or falls through 0DF into the existing 1D3 tail.

This retains q3, previous flags, zero reset, matched PLP replies and table
index two. Selector 1 is explicitly changed from constant false to a scheduled
external line. It starts low and rises at a predicted instruction cycle; no
runtime PC or stack state is changed by the harness. Physical condition wiring
and input channel meanings remain unknown.

## Preserved prefix and transition times

The existing [handler-6 analysis](HANDLER6.md) supplies code c=6 mod 8 and
captured byte x. Define:

```
m0 = x & (c+1)
t = (m0 + int(m0!=0)) & 255
h = t >> 1
B = 115 + 2*(bit_length(((c+2)&255)>>1)+1) + int(c==254)
```

B is the baseline first-terminal cycle. Before the new continuation, R7=x,
R13=t and R15=h. The two schedules are:

- Capture route: raise selector 1 at B-30, when 0C7 executes. It takes 0E5,
  returns through 0E8 to 0C8, and later also takes 0CB to 0CE.
- Late route: raise it at B-26, when 0CB executes. 0C7 retains its original
  fallthrough, so execution enters 0CE without the additional capture.

The study compares every instruction before the transition with the unchanged
baseline for the same c/x: PCs, next PCs, ALU results, RAM writes, Q and full
stack values match. Only external-condition metadata and scenario provenance
differ. Later inputs cannot explain away a changed prefix.

## Input capture and overwritten values

Let a=D0E5, u=D0CF and v=D0D4. On the capture route, 0C7's XNOR supplies carry
one to 0E5. With Q=0, 0E5 writes R5=(a+1)&255. 0E6 forms a temporary R3
difference from R15; 0E7 loads an external value into R12. Both are later
overwritten, and 0E8 branches to 0C8. On the late route R5 remains zero.
Call this retained intermediate value s:

```
s = (a+1)&255 on capture route, otherwise 0
```

At 0CE, Q is loaded from zero R0. The preceding noncarry makes its TSK allow
0CF, which loads u into Q. 0D0 temporarily masks Q with R2; 0D2 copies R5=s
into R3. 0D3 clears R8, then 0D4 overwrites R0 with m=u AND v.

0D5 writes Q=(m+int(m!=0))&255, using the logical carry from 0D4. 0D6 captures
that addition's carry into R2. The later R1+R2 sum cannot carry, so 0DA does
not take 1DC in these contexts. 0DB/0DC expose transient values before 0DD's
real call to 04C.

The 04C helper clears Q and copies R3=s into R12. Its last instruction, 053,
exposes R0 AND R12 = m AND s. Under previous-zero timing, that result selects
the branch at 0DE. R5's value is therefore useful through its copy into R12,
even though the terminal helpers later clear R5.

## Exit selection and complete state

If m AND s is zero, 0DE branches to 079. R3=s, R4=2 and R12=s survive the
terminal sequence. If it is nonzero, 0DE falls through to 0DF, which branches
to 1D3. That tail copies R0=m into R4, clears R3 from zero R1 and enters the
terminal sequence at 07A.

For either route the complete final state is:

| Register | Value |
| --- | --- |
| Q | 0 |
| R3 | s on the normal exit, otherwise 0 |
| R4 | 2 on the normal exit, otherwise m |
| R7 | x |
| R12 | s |
| R13 | t |
| R15 | h |
| All other RAM registers | 0 |

Maximum stack depth is two and final depth is zero. An exhaustive local check
of the actual 053 operation covers all 65,536 m/s pairs: 6,561 select the
normal exit and 58,975 select the alternative. This counts operand pairs,
not the distribution of real hardware inputs.

## Timing and the extra terminal step

Starting from B, add 26 cycles for the capture route or 22 for the late route.
Add eight more if m AND s is nonzero and execution goes through 0DF/1D3.

There is one additional boundary case on the normal exit. Although 0DE tests
053's previous zero flag, it also computes XNOR(R0,R15). If m is the bytewise
complement of h, that result is zero. The following 079 then does not skip
07A, adding one instruction. Otherwise it skips directly to 07B. 07A has no
retained write, so the state table above is unchanged.

```
first_terminal = B + (26 if capture else 22)
                   + 8*int((m&s)!=0)
                   + int((m&s)==0 and m==(h^255))
```

This illustrates why the branch's tested flag and its own arithmetic result
must both be tracked. Terminal arrival is not a physical completion signal.

## Evidence and scope

The study executes 2,048 complete 192-instruction reset cases: all 32 codes,
zero/FF captured bytes, both schedules, four capture inputs and four u/v
boundary pairs. Randomized regressions vary all captured/input bytes
independently and explicitly include the extra-terminal-step boundary.
Eight full reset witnesses cover both continuations, both exit types and
capture wraparound; they replay byte for byte.

Every run checks complete final RAM/Q, intermediate mask and increment,
entry transfers, helper call/return, terminal timing, stack depth and unchanged
prefix. The bodies 0E0–0E4 and 0E9 onward are not assigned the same meaning,
and 1DC remains excluded by the checked noncarry argument.

[Configuration](handler6-late.json), [runner](handler6_late.py), and
[report](results/handler6-late/report.json).

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/handler6_late.py
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -p 'test_*.py'
```
