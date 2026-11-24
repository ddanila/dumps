# Handler 0: fixed-register waits and transient arithmetic

*Runs under the [shared assumptions](ASSUMPTIONS.md).*

Under q3 with current flags and the established BLT-side reset replies,
handler 11A returns through both fixed-register waits and calls the later
arithmetic helpers. The complete retained effect is small: R4 retains the
input-code/capture sum, Q becomes FF, and the terminal stores put 127 in R2.
Several intermediate input values affect arithmetic without surviving in RAM/Q.
This describes an explicit execution hypothesis, not a recovered modem mode.

## Why changing external bytes cannot release the waits

The q3 loops at 127–12A and 12C–12F copy R1 into R2 and clear Q using zero
AND Q. The following instruction exposes R0 and produces carry one. BLT
then exposes R0+1 modulo 256. Neither loop writes R0 or selects external D.
The select-0 nonzero condition therefore gives these exact predicates:

| Timing | Returns | Otherwise |
| --- | --- | --- |
| Previous flags | R0=00 | Repeats with period four |
| Current flags | R0=FF | Repeats with period four |

These are not the fitted-original mapping's bit-containment tests described
in [MASK-LOOP.md](MASK-LOOP.md). In q3 the source is zero/Q, not R0/Q.
Every R0 byte is checked for both helpers and timings using actual calls at
11B or 11D, with nonzero RAM/Q fixtures and no injected stack frames. Only
one of 256 R0 values returns in each configuration. The remaining 255 repeat
the same modeled state after four instructions. RAM is unchanged apart from
R2=old R1; Q is zero while repeating. A returning 126 reloads Q from D12B,
whereas returning 12C leaves Q zero. These checks cover 1,024 local calls.

Zero reset reaches handler 0 with R0=FF. Previous flags thus prevent reaching
11C for any later external reads; current flags allow both waits to return
on their first pass. This comparison keeps the alternative timing explicit.
The matched early reply schedules also differ, and current timing leaves
R6=R7=FF, so the two reset contexts are not interchangeable.

## Complete current-timing path

Input code c=0,8,...,248 selects 11A. An independent byte d at 115 establishes
R4=(c+d) modulo 256. Other later dispatches use the established index two.
Independent inputs b, a and t are supplied at 126, 12B and 271 respectively.

The actual helper entry order is:

```
126 → 09A → 12C → 09A → 270 → 238 → 131 → 240 → 131
```

126 temporarily produces Q=c+b, but 128 clears it. The return at 12B loads
Q=a; the second loop clears it again. The 09A calls each copy R1=0 to R2,
and 11F saves that zero in R12.

270 loads Q=t. In this current-flag context, the zero-producing AND at 272
skips 273, the XNOR at 278 branches to 27B, and the zero-producing AND at
27D skips 27E. R0 remains FF. This is a separate branch argument from the
previous-flag contract in [BRANCH-HELPERS.md](BRANCH-HELPERS.md).

238 and 240 expose the subtract-one/carry-adjusted pair in different orders.
Both copy R4 into R2 and R0 into Q. Thus 238 overwrites t with FF, and 240
keeps Q=FF. The two 131 calls expose R4+R12 and R0 AND R12 without storing
those results. No external consumer is assigned to these transient Y values.

125 branches to 079. The true selector-5 skip bypasses 07A, and terminal
helpers shift Q into R0 before each indexed R2 store. Terminal entry therefore
has this complete RAM/Q contract:

- Q=FF.
- R0=R2=127.
- R4=(c+d) modulo 256.
- R6=R7=FF from the early reset replies.
- All other RAM registers are zero.

The first 084 execution is cycle 126, independent of b, a and t. Maximum
stack depth is two and final depth is zero. Transient arithmetic still depends
on those discarded inputs; no claim of identical I/O traces is made.

## Evidence and scope

[The study](handler0_study.py) checks the local timing predicates and 2,048
complete 160-instruction reset cases: all 32 handler codes and four boundary
values each for d, a and t, with b=d XOR t. Four saved reset witnesses cover
codes 00/F8 and captures 00/FF. Randomized regression cases vary all four
input bytes independently to break that correlation.

Each reset case checks every final RAM/Q value, intermediate Q writes,
helper order, branch choices, terminal cycle and stack depths. The fixed-register
loops are not externally releasable in this model, and current timing is not
promoted to hardware truth merely because it allows this handler to finish.
Other handlers can repeat under the same timing, as shown by
[HANDLER-TIMING.md](HANDLER-TIMING.md).

[Configuration](handler0-study.json) and [report](results/handler0-study/report.json).

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/handler0_study.py
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -p 'test_*.py'
```
