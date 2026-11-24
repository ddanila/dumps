# Three q3 handler-5 continuations

*Runs under the [shared assumptions](ASSUMPTIONS.md).*

The three declared cases at 34C compose the already checked 335, 357 and 366
helpers differently. From actual zero reset they select Q=0, Q=the input code,
or Q=FF, and different external inputs survive in R4. All three enter the
terminal sequence at 07B, preserving the R3 value written by the carry helper.

This study uses q3, previous flags and the established PLP-side early replies.
Input codes `c=5,13,...,253` select handler 345. Other external reads are one,
except the reset code inputs and three independent parameters:

- u is read at 336.
- v is read at 359.
- m is read at 354.

The global scenario table index i=0,1,2 selects both the initial paired row and
the continuation at 34C. The two terminal stores are independently selected
through preceding Y: D089=2 directs both to R2. These are explicit dispatch
and input hypotheses, not recovered physical command fields.

## Common preparation and initial paired call

345 calls 314, leaving R4=R13=c+1. 346 calls 389, copying R4–R7 into R8–R11.
R6/R7 are zero in these fixtures. The first paired table exposes two 16-bit
results: row zero emits `2*(c+1), 0`; rows one and two emit `0, 0`. Their final
high byte is zero, so every initial call returns after one pass, even when the
first result has a nonzero high byte.

347's R7 copy into R2 is overwritten by 348's R3 copy and then by 349's input
sum. That temporary R2 is subsequently overwritten by the carry helper and
terminal stores. 34C selects 34D, 34E or the fallthrough body beginning at 34F.
The actual table targets and transitions are checked in each reset run.

The earlier [controller-to-DAC bridge](FRAME-DAC-BRIDGE.md) supplied nonzero
captured R6/R7 and a different paired entry, making its first paired call
repeat. It never reached these continuations. This study therefore complements
that recurring-output case rather than treating its state as interchangeable.

## Continuation composition

| Entry | Path | Helper entry order | Final Q | Final R4 | First 084 cycle |
| --- | --- | --- | --- | --- | ---: |
| 0 | 34D → 361 | 366, 357, 335, 357 | 0 | v | 129 |
| 1 | 34E → 353 | 366, 357 | c | `(v+c)&255` | 109 |
| 2 | 34F | 335, 366 | FF | u | 110 |

**Entry 0.** 366 receives R0=FF and returns with R1=0, R2=2, R3=3 and R0=1
while preserving Q=c. The first 357 copies R1 into R0, so R0 becomes zero.
363 computes R0−1 into Q, giving FF; 335 complements it to zero. 365 continues
to 354. Its mask result is zero because Q is zero. The second 357 writes
R4=v+Q=v, overwriting the earlier R4 captures, and again copies R1=0 to R0.

**Entry 1.** 366 again produces R1=0, R2=2 and R3=3. Q remains c. 354 writes
m AND c to R0, but 357 immediately overwrites R0 with R1=0 and writes
R4=v+c modulo 256. The mask affects an intermediate value but has no surviving
RAM/Q effect at terminal entry.

**Entry 2.** 34F first sets Q=R0+1 modulo 256. Since the reset prefix has
R0=FF, Q becomes zero. 335 captures u in R4 and complements Q to FF. 366
preserves that Q, returns R0=1, and leaves R1=0, R2=2, R3=3. It does not alter
R4, so u survives.

All 335 calls use the existing true selector 5 and false selector 6: optional
R0/R12 captures are bypassed and Q is complemented. All 357 calls use true
selector 5 and return through 360. The 366 carry loop sees D36C=D36D=D36E=1
and incoming R0=FF; its middle addition does not carry, so it returns after
one iteration. The model uses real calls and POPs, with maximum stack depth
three and final depth zero.

## Terminal entry matters

Each continuation branches to **07B**, bypassing the earlier 078–07A
preparation. Consequently the R3=3 from 366 survives; formulas that include
the earlier R3/R15 writes would be wrong for these paths. R12 and R15 remain
zero.

For final Q selected by the table above, the complete terminal state is:

- R0=R2=Q>>1, from the two actual R2 stores.
- R3=3.
- R4 is the table's surviving input value.
- R5=`((-Q)&255)>>1`.
- R8=R13=c+1.
- Every other RAM register is zero.

The same formula gives R5=0 in entries zero and two and `(255-c)>>1` in
entry one. Q is preserved by the terminal helpers. 316's transient input sum
does not write R12 under this decode, so R12 must not be inferred to contain
c+1 merely because the earlier preparation exposes that value.

## Verification

The study executes 1,536 complete 160-instruction reset runs: all 32 codes,
three continuation indices, four u values and four v values. The sampled
values include zero, one, high-bit and FF boundaries; m is explicitly u XOR v.
Each case checks every final RAM/Q value, first-terminal cycle, helper-call
order, both terminal dispatches, initial paired outputs, the intermediate
354 mask, and stack depth.

Forty-eight independently randomized regression cases vary c, u, v and m.
Each is also rerun with all mask bits flipped, checking the predicted lack of
retained effect. This breaks correlations in the main sweep. Tests explicitly
preserve R3=3 and R12=R15=0, preventing an accidental reuse of the wrong
terminal-entry contract.

Six saved witnesses cover all three continuations at codes 05 and FD. The
sweep is not an exhaustive all-input or all-initial-state analysis. It does
not assign a physical consumer to transient outputs or identify a modem mode
for any of the three table cases.

[Configuration](handler5-branches.json), [runner](handler5_branches.py), and
[report and witnesses](results/handler5-branches/report.json).

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/handler5_branches.py
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -p 'test_*.py'
```
