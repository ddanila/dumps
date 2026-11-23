# Carry-controlled three-add loop at 36C

Under the fitted-original decode, 36C–36E performs three chained byte additions,
with one carry forwarded between the first two. It preserves R0 and Q.
Repeating the loop does not count down either register. Whether it exits is
sensitive to the assumed timing of the condition flags.

Let A be initial R0 and D0/D1/D2 the external operands supplied at the three
instructions. All stored values wrap to eight bits:

```
T0 = A + D0             R1 = T0 mod 256
T1 = R1 + D1 + carry(T0) R2 = T1 mod 256
T2 = R2 + D2            R3 = T2 mod 256
```

Carry is one when a total exceeds 255. The first carry feeds T1 through the
existing mapped-or-previous carry policy; T2 has carry input zero. The ALU Y
outputs are **A, R1, R2**, because these instructions select the old A-register
value for Y while storing the sum. They are not the same as the three stored
sums, and no physical output consumer is identified.

PLP at 36C pushes the loop address; BLT at 36E pops it on either outcome.
Under previous-flag timing, BLT repeats when T1 produces carry. Under current
flag timing, it repeats when T2 produces carry. With constant A and the same
three external operands on each pass, a repeated pass reproduces the entire
modeled loop state exactly. R0/Q do not supply a hidden iteration counter.

## Local verification

[carry_chain_study.py](carry_chain_study.py) tests all 65,536 A/D pairs with
D0=D1=D2, plus 4,096 seeded combinations with independently varied operands,
under both flag timings: **139,264 local comparisons**. It checks all register
RAM, unchanged Q, all three ALU-Y values and carries, balanced stack actions,
exit PC, and exact repeated-state equality. Thirty-two representative cases
also replay through the ordinary integrated executor.

| Timing | Constant-input cases exiting | Constant-input cases repeating |
| --- | ---: | ---: |
| Previous flag | 32,768 | 32,768 |
| Current flag | 32,897 | 32,639 |

The two timings disagree on 32,725 constant-input cases. This is a local
hypothesis comparison, not evidence selecting either wiring. The default
previous-flag scenario remains unchanged. The fixture stops at 36F on exit;
it does not execute that following POP without a caller return address.

## Connection to reset dispatch

The [current-Y dispatch experiment](DISPATCH109.md) sends inputs D=04,0C,...,FC
through entry 5 at 109, then to 345. The new study replays all 32 such reset
paths. At their first entry to 36C, R0=255−D, still last written by 074. No
intervening setup instruction replaces it. With D held constant:

```
R1 = FF, carry(T0) = 0
R2 = D−1, carry(T1) = 1
R3 = (2*D−1) mod 256
```

Thus the selected previous-flag policy repeats for all 32 inputs, explaining
the three-instruction cycle observed in the dispatch report. For these same
local entry operands, current-flag timing would exit for the 16 inputs below
80 and repeat for the 16 above it. This is not a claim that globally changing
flag timing preserves the preceding reset path.

The reset checker records the last R0 writer and the first three full trace
rows, including Y outputs, carry inputs and the actual loop branch. Four reset
witnesses retain complete 256-cycle traces.

## Reproduction and limits

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/carry_chain_study.py
```

[Configuration](carry-chain-study.json) declares the model, initial register
fixture, independent-input sweep and reset inputs. The
[report](results/carry-chain-study/report.json) stores counts, timing differences,
local and reset witnesses, source hashes and an execution digest.

This names a concrete arithmetic/control structure under the candidate decode.
Its external operands and Y-output consumers remain unidentified. Different
operands on subsequent iterations could change the carry and release the loop;
a constant-input repeated state does not by itself establish a real hardware
hang, nor does this structure establish a multiply, filter, or sample timer.
