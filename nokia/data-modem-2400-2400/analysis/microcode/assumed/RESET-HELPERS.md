# q3 reset preparation helpers 06F and 112

*Runs under the [shared assumptions](ASSUMPTIONS.md).*

These two direct-call helpers prepare registers before the early external waits
and handler dispatch. Their complete retained state is predictable under q3,
including nonzero initial registers. The local experiments use real BSR/POP
instructions with an initially empty stack; a separate unchanged reset replay
checks the actual caller state. Neither helper is identified as a modem
algorithm or a physical input protocol.

## 06F: carry-selected half/difference and input accumulation

Let r be incoming R9, q be incoming Q, and d be the input byte read at 076.
Only R0, R2 and Q change:

| Result | Formula |
| --- | --- |
| R0, r=00–7F | `255-(r>>1)` |
| R0, r=80–FE | `(r+1)>>1` |
| R0, r=FF | 0 |
| R2 | incoming R8 |
| Q | `(q+d)&255` |

All other RAM is preserved. The unusual piecewise R0 transformation follows
the carry and skip sequence, rather than an assumed signed divide:

- 070 forms `R0=(r+1)&FF`.
- 072 adds r and that wrapped byte, setting carry for r=80–FE only.
- 073 right-shifts R0 and tests the preceding carry. It skips 074 on that
  interval. The XOR operation at 073 itself leaves carry zero.
- If executed, 074 writes `R0=R0-r-1 mod 256` using that zero carry. In
  particular, FF wraps at 070 and follows the subtraction path to zero.
- 075 copies R8 into R2; 076 accumulates d into Q; 077 ANDs R8 with its
  copied value, preserving R2 and exposing R8 on Y before returning.

The representative input/output pairs are `00→FF`, `7F→C0`, `80→40`,
`FE→7F`, and `FF→00`. The helper takes eight instructions for r=80–FE and
nine otherwise. Including the caller adds one instruction.

The actual direct callers are 004 and 101. Local validation starts at 004;
the saved zero-reset witness enters through 101. No return address is manually
inserted in either execution.

## 112: negate R0 and capture D+Q

Let d be the byte read at 115. On return:

```
R2 = -incoming_R0 mod 256
R4 = d + incoming_Q mod 256
Q  = incoming_Q
```

All other RAM is unchanged. 112 initially copies R1 into R2, but 116 replaces
it with the negation of R0. The intermediate arithmetic at 113–114 does not
survive in RAM/Q. The final Y result is the negated R0. This five-instruction
helper always returns; local checks include its real caller at 102 for six
instructions total. The other direct caller is 104.

## Connection to the reset path

The unchanged handler-1 reset scenario provides three calls:

| Helper | Entry/return cycles | Selected input | Result relevant to the next stage |
| --- | --- | --- | --- |
| 06F | 6–14 | 5C | R9=0 gives R0=FF; Q=A5+5C wraps to 01 |
| 112 | 16–20 | 01 | R2=1, R4=2, Q=1 |
| 112 | 28–32 | 01 | R2=1, R4=2, Q=1 |

Cycles are decimal and byte values are hexadecimal. The two 112 calls preserve
the same prepared values around the external wait. This explains the FF/1
register preconditions used by later handler studies. The scenario's zero
initial RAM makes R8/R9 zero; these experiments do not establish that physical
power-on hardware clears those registers.

## Validation and limitations

Each helper is checked on two 65,536-case planes:

1. Every relevant input register (R9 or R0) against every initial Q, with d=1.
2. Every input d against every initial Q, with that register held at FF.

Thus 262,144 local calls check complete final RAM/Q and instruction count.
Other RAM begins with distinct nonzero values, including a varying R8, so
preservation and overwritten temporaries are tested. These planes are not
claimed as the full three-dimensional register/Q/d space. Ten selected main
executor runs match each local trace step, including flags, stack slots and
register changes. The 512-cycle reset witness reproduces all five saved files
byte for byte and its three helper calls match the formulas.

The interpretation is scoped to q3, the selected previous-flag policy and
zero-fill shifts. It names computational behavior without assigning physical
meanings to R8/R9 or the two external input sites. In particular, the sharp
7F/80 boundary remains a prediction of this candidate mapping.

[Configuration](reset-helpers-study.json), [runner](reset_helpers_study.py),
[report and witnesses](results/reset-helpers-study/report.json).

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/reset_helpers_study.py
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -p 'test_*.py'
```
