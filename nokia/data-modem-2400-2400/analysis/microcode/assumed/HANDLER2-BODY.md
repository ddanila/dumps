# Handler 2: comparison preparation, Q drains and payload storage

*Runs under the [shared assumptions](ASSUMPTIONS.md).*

This study connects the q3 handler at 18B through its long preparation body,
the paired-drain detour, the external poll and terminal stores. Three independent
input bytes expose distinct effects: one selects the retained comparison byte,
the sum of two controls execution time, and the last becomes the stored payload.
The model uses previous flags, PLP-side early replies, zero reset, and later
table index two. It does not assign physical meanings to these input channels.

## Inputs and complete result

The code c=2,10,...,250 selects handler 18B. Define:

- a = D197, an input loaded after the early arithmetic calls.
- b = D1A2, added to Q by the computed call instruction.
- p = D1D0, the payload loaded after the captured-register arithmetic call.
- k = number of deliberately unsuccessful external poll replies.

With every other read held at the established defaults, the contract is:

```
r = 254 + (1 if (a & 254) != 0 else 0)
s = (a+b) & 255
release reply = (-r) & 255
first poll cycle = 181 + 2*bit_length(s)
first terminal cycle = 213 + 2*bit_length(s) + 2*k
```

Here bit_length(0)=0. Final Q=p, R0=R2=p>>1, R5=((-p)&255)>>1,
and R12=r. Every other RAM register is zero. These formulas include byte
wraparound: a+b=256 drains zero, rather than a nine-bit sum. They apply to
all 32 handler codes under this reset scenario, not arbitrary caller states.

## From handler entry to the retained comparison byte

18B calls 341 to copy Q=c into R0. The zero-source, fixed-entry transform at
3EA returns after one table pass. 18D then restores R3=1 from the reset
preparation's R2. The 270, 238 and 240 calls leave R0=c and ultimately Q=c;
the interleaved 191/194 operations preserve R0. Since c is nonzero, 195 does
not take the previous-zero branch to 1E0.

196 clears Q from zero R8, and 197 loads a. 199 and 19B expose/store a AND FE;
19A clears R8. Crucially, 19B also produces logical carry one exactly when
(a AND FE) is nonzero. 19C consumes that carry while subtracting R3=1 from
zero with borrow convention, yielding R4=FE or FF. Its R4 write overwrites
the preceding mask result, but retains one bit of information through carry.

Thus a=0 or 1 requires poll reply 02. Every other a requires reply 01.
The earlier [reply study](HANDLER-REPLY.md) held a=1 and correctly found only
02 in that context; it was not a universal handler-2 reply value.

19D–1A1 expose additional input and register arithmetic without changing the
retained R4. 19E copies zero R10 into R2. At 1A2, Q becomes s. The declared
computed-call table overrides the encoded target 300: index two actually
calls the single-instruction POP leaf **1E7**. Its temporary R3 result depends
on the addition carry and is subsequently overwritten. The table association
is an explicit hypothesis inherited from the scenario.

## Drains and the paired arithmetic detour

1A3 calls 1E9 with Q=s. Under previous-zero timing its loop performs
bit_length(s)+1 iterations, including the final zero test. Each iteration
costs two instructions. 1A4/1A5 clear R0, and 1A6 drains the already-zero Q.
The following block clears Q again and copies zero R13 into R0 and R3.
Several temporary shifts and differences are overwritten; 1B5 leaves R0=FE
under the default reads.

The selector-1 branches at 1B8, 1B9, 1BC and 1BD are false. 1BE copies zero
R10 to R15, and 1C0's noncarrying R0 exposure makes the previous-carry branch
at 1C1 false. The true selector-5 branch at 1C2 takes **2D0**, bypassing
1C3–1CC. That detour performs the established two Q drains and branches to
1CD. This study does not claim to interpret the bypassed alternative body or
1DA–1DE.

1CD/1CE leave R0 zero. 1CF calls 3A2, whose capture sequence preserves R4
in R12 and copies the zero second-component registers into R13–R15. Its
fixed paired table returns after one pass, preserving the comparison value.
The captured R12 survives all subsequent terminal operations.

## Reply and terminal storage

1D0 loads p into Q. 1D1 clears R0 before 1D2 calls the external poll. The poll
at 1EC computes R3=D+R4 modulo 256, so only D=-r returns. Each deliberate
failure supplies release+1, produces R3=1 and adds two cycles. The successful
reply leaves R3 zero and preserves Q=p.

After return, 1D3 clears R4 by copying R0; 1D5 copies zero R1 to R3; 1D7
halves Q into R0 without changing Q. 1D9 enters the terminal sequence at 07A.
Two fixed-index stores select R2, while the shift helpers leave R0=p>>1 and
R5=((-p)&255)>>1. Maximum stack depth is three, with no remaining frame at
terminal 084. Reaching 084 is an emulator control-flow result, not a recovered
physical completion signal.

## Verification

The local arithmetic check evaluates all **65,536 a/b pairs** with the actual
Am2901 operations at 19B, 19C and 1A2 against the independent formulas. The
full study runs **2,048 reset cases**: all 32 codes and boundary values for
a, b and p, with zero, one or two unsuccessful replies. It checks the complete
final RAM/Q, first-poll and terminal timing, computed-call target, detour,
R12 capture and stack depths. Four full witnesses cover both comparison
values at codes 02 and FA and replay byte for byte.

Randomized regression cases vary all input bytes and reply delay independently.
The sampled reset sweep is not an exhaustive arbitrary-state proof. Fixed
selectors, early replies and table choices remain labelled assumptions, and
transient Y outputs have no assigned external consumer.

[Configuration](handler2-body.json), [runner](handler2_body.py), and
[report](results/handler2-body/report.json).

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/handler2_body.py
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -p 'test_*.py'
```
