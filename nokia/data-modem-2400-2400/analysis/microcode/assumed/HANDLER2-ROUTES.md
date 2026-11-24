# Handler 2: timed continuation choices and carry-biased drains

A scheduled external condition reaches the alternative body 1C3–1CC from
actual zero reset. Four earlier condition points also reach this body through
1DA's call to 341. These paths preserve the same final register contract as
the existing 2D0 detour, but their first Q loads and execution times differ.
No branch destination, PC or stack frame is patched.

## Condition schedules

The base is [handler 2's previous-flag body](HANDLER2-BODY.md), with inputs
a=D197, b=D1A2 and payload p=D1D0, fixed later table index two, and matched
PLP-side reset replies. Let L=bit_length((a+b)&255). The first branch at 1B8
occurs at cycle t=134+2L. Two separately declared selector hypotheses give:

| Route | Scheduled line | Result |
| --- | --- | --- |
| detour | Selector 5 starts high, falls at t+11 | 1C2 at t+10 still takes 2D0 |
| fallthrough | Selector 5 starts high, falls at t+10 | 1C2 enters 1C3 |
| prepare-1b8 | Selector 1 rises at t | 1B8 takes 1DA |
| prepare-1b9 | Selector 1 rises at t+1 | 1B9 takes 1DA |
| prepare-1bc | Selector 1 rises at t+4 | 1BC takes 1DA |
| prepare-1bd | Selector 1 rises at t+5 | 1BD takes 1DA |

Selector 1 starts low in its four scenarios; selector 5 retains its original
constant-true policy there. Each external input is an absolute-cycle event
list, interpreted by the normal executor and logged whenever consulted. The
schedule is computed before execution from the timing formula. It neither
observes the runtime PC nor forces a transfer. The line's physical pin and
clock remain unknown.

The adjacent fall times around 1C2 demonstrate an actual timing boundary:
falling one cycle later leaves the detour selected. The selector-1 experiments
preserve earlier boot and preparation conditions until the chosen branch.
They do not establish that the real board uses either selector in this way.

## Alternative preparation and arithmetic

In the four preparation routes, 1DA calls 341 with Q=0. That helper copies Q
into R0, clearing the FE left by 1B5. 1DB then branches to 1C3. The later Q
drains overwrite R0 in either case, so this preparatory difference does not
survive terminal execution. The routes skip different portions of 1B8–1C2,
which accounts for their distinct timing.

1C3 and 1C4 expose R5 without a retained write. Their noncarrying arithmetic
makes the carry input at 1C5 zero. Supply the same byte u at 1C5 and 2D0, and
the same byte v at 1CA and 2D5, to compare corresponding input channels:

| Route | Q before first shift | Q entering first 1E9 drain | Q entering second drain |
| --- | --- | --- | --- |
| 2D0 detour | (u+1)&255 | ((u+1)&255)>>1 | v>>1 |
| 1C3 body | u | u>>1 | v>>1 |

The detour's extra one is carry feedback from 1C2. The fallthrough body has
no such carry at 1C5. Both routes halve Q before their first 1E9 call. After
return they clear R0, load the second Q input, halve Q again, and drain it.
1C8/1C9 and 1CD/1CE overwrite the temporary R0 values. The body joins at 1CD
by fallthrough; the detour joins through the actual 2D8 branch.

The Q shifts use the pre-shift Q value, even where the simultaneous RAM
arithmetic adds one. This distinction matters at FF: the detour wraps its
initial Q load to zero, while the alternative body enters its drain with 7F.

## Complete state and timing

Define H(x)=bit_length(x>>1), with H(0)=0. The first-poll cycles are:

```
detour:       179 + 2L + 2H((u+1)&255) + 2H(v)
fallthrough:  180 + 2L + 2H(u)         + 2H(v)
```

For preparation routes, start with the fallthrough formula and add -4, -3,
0 or +1 for branch 1B8, 1B9, 1BC or 1BD respectively. Each of k failed poll
replies adds two cycles; the first terminal 084 cycle is first_poll+32+2k.
With u=FF the detour reaches the poll 15 cycles before fallthrough; with u=1
it reaches it one cycle later. Thus a blanket timing offset would be wrong.

All six routes retain the same final state:

- Q=p; R0=R2=p>>1; R5=((-p)&255)>>1.
- R12=254+int((a&254)!=0), with release reply equal to its byte negation.
- Every other RAM register is zero.

Maximum stack depth remains three and final depth is zero. Equal retained
state does not imply equal transient output values or equal I/O timing.
The bodies at 1DC–1DE remain outside this study.

## Evidence

The study executes 3,072 complete 384-instruction reset cases: all 32 handler
codes, six condition schedules, and four boundary values each for u and v.
The main sweep derives a, b and p from the chosen bytes; randomized regressions
vary them independently and add explicit zero/wrapped-sum cases. Every run
checks complete final RAM/Q, the Q values before and after both shifts, actual
branch/call targets, event values, first-poll and terminal cycles, and stack
depths. Six saved witnesses include the FF wrap boundary for every route.

All input routing, line assignments and table choices remain explicit
hypotheses. This is a checked continuation comparison, not an identification
of a modem mode or an analog output consumer.

[Configuration](handler2-routes.json), [runner](handler2_routes.py), and
[report](results/handler2-routes/report.json).

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/handler2_routes.py
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -p 'test_*.py'
```
