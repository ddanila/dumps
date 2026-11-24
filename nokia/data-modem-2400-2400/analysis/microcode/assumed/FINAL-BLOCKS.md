# Final branch blocks: early clear/capture and current-flag exit

*Runs under the [shared assumptions](ASSUMPTIONS.md).*

The last five previously unannotated words belong to two separate calling
contexts. 043/044 expose an input difference and call a helper that clears Q
and captures R3. 1DC–1DE expose arithmetic and select between two terminal
entries under current-flag timing. These interpretations do not combine the
contexts into one condition-policy claim.

## 043–044: capture the comparison and clear Q

Use the [early 032 study](EARLY-ENTRY32.md), first index 2, q3 and previous
flags. Supply a at 033, b at 034, g at 043, x at 05B and y at 064. Its
existing input path leaves Q=1 and R3=r=(b-2+int(a!=0))&FF. At 041, R1 and
R15 are both zero, so their sum has carry zero. The original selector-3
inverted-carry policy therefore makes 042 jump to 045; it excludes 043.

The alternative explicitly changes selector 3 to inverted external input.
The line starts at zero and rises at cycle 26, the execution of 042. That
makes the branch false and admits 043. PC, ALU, RAM/Q and stack transitions
before cycle 26 match the original case. Keeping the carry source, or moving
the rise to cycle 27, still jumps to 045. This is a condition-source hypothesis,
not a claim about the physical multiplexer.

043 exposes (g-2)&FF without storing it. The previous carry from 042 is zero;
its current subtraction does not select a branch. 044 calls the already
checked [04C helper](SHORT-HELPERS.md) with a real return frame. That helper
clears Q at 050, copies R3=r into R12 at 051, and exposes R0 AND R12=0 at
053. It returns to 045, whose previous-zero test goes directly to 05B.

Consequently the shared 05D wait now compares **Q=0** against R3=r, rather
than the original Q=1. It first executes at cycle 40. If r is nonzero it
repeats with period seven, leaving Q=0, R0=1, R2=R3=R12=r and R4=x;
all other RAM is zero. The active loop frame remains at depth one.

If r=0, the wait exits on its first pass and reaches terminal 084 at cycle
58. Q=0, R0=R2=1, R3=(y-1)&FF and R4=x; other RAM is zero, including R12.
The active stack is empty. Both outcomes have maximum depth one. Thus the
helper changes which input comparison releases the wait and retains that
comparison separately in R12. g changes only transient output.

The reset sweep covers a=0/1, every b and two independent capture/tail pairs:
1,024 cases, with 16 original-source/late-rise controls. Random regression
also varies arbitrary a, g, capture and tail bytes. Recurrence checks preserve
stack slots, flags and input cursors, not merely PC repetition.

## 1DC–1DE: current subtraction carry and complement selection

This study uses q3 with the existing **current-flag** option and the matched
BLT-side early replies. Both startup capture registers R6/R7 become FF. Code
c is congruent to 6 modulo 8. Let:

```
t = (c+2)&FF
h = t >> 1
T = 78 + 2*max(1, bit_length(h))
```

Selector 1 is a direct external line, initially low, rising at cycle T when
0C0 executes. Prefixes match the original current-flag reset run up to that
cycle. This takes the existing 0E0 diversion, whose complement at 0E1 makes
Q=FF. Supply d at 0C6, a at 0E5 and v at 0D4.

The input mask at 0C6 loads R0=d. 0E5 captures (a-1)&FF, later copied into
R3. 0C8/0C9 leave R12=h; R13=t and R15=h retain the earlier preparation.
0CE copies R0 into Q and its own operation produces carry one. Under current
flags it therefore **always skips 0CF**, preserving Q=d. This differs from
the [previous-flag early diversion](HANDLER6-EARLY.md).

At 0D4, m=d AND v is stored in R0. Logical carry increments it at 0D5:
Q=q=(m+int(m!=0))&FF. 0D6 leaves R2=int(m==FF), so 0D9's exposure of R1+R2
cannot carry. Under previous flags, 0DA would test this zero carry and continue
to 0DB. Under current flags it tests its own subtraction R7-R0=FF-m, whose
carry is always one. It consequently branches to 1DC for every mask byte.
The matched previous-flag controls confirm that same current carry can be one
while their branch still continues to 0DB.

1DC exposes R2+Q. This has no carry for any m, including the FF wrap case
where R2=1 and Q=0. It changes no retained state. 1DD exposes XNOR(R0,R15)
and tests its **current zero flag**, so:

| Condition | Path | Retained R3/R4 |
| --- | --- | --- |
| m == h XOR FF | 1DD → 079 → 07B | R3=(a-1)&FF, R4=2 |
| Otherwise | 1DD → 1DE → 1D3 … 1D9 → 07A | R3=0, R4=m |

1DE exposes a carry-adjusted Q-R0 difference without storing it and takes its
unconditional branch. On the direct path, 079's current Q-1 result is nonzero:
q can be zero or 2–FF, but never one. Thus 079 always skips 07A here. There
is no call to 04C on either path, so R12 remains h and Q is not cleared.

## Current-flag complete state and timing

At terminal, Q=q. R0=R2=q>>1, R5=((-q)&FF)>>1, R6=R7=FF, R12=R15=h and
R13=t. R3/R4 follow the table above; all other RAM is zero. First execution of
084 is T+54 on the complement-match path and T+62 otherwise. Maximum stack
depth is two, with no active frame at terminal. These are microinstruction
counts, not sample rates.

The reset sweep uses all 32 codes, independent mask factors covering zero,
FF and each complement boundary, and three capture bytes: 570 distinct cases.
Thirty-two matched previous-flag controls retain the 0DA→0DB exclusion. The
local check executes 0DA/1DC/1DD for every m/h pair (65,536 cases), checking
both carries, the complement predicate and complete retained-state preservation.
Random regression varies d/a/v independently and changes bypassed 0CF and
overwritten 0E2/0E3 inputs without changing the result.

## Evidence and limits

Eight saved witnesses cover both early wait outcomes, both current-flag exits
and the FF wrap boundary. All are zero-reset executions with real stack
operations. The current and previous timing policies remain explicit alternatives;
the early selector-3 source change is also explicit. No arbitrary initial-state
or physical-function claim follows from these successful contexts.

These annotations close the listing's word-level gaps. They do not by
themselves complete the program-level reading or the plan's final audit.

[Configuration](final-blocks.json), [runner](final_blocks.py),
[report and witnesses](results/final-blocks/report.json).

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/final_blocks.py
```
