# Two Q drains explain the variable time before polling

*Runs under the [shared assumptions](ASSUMPTIONS.md).*

Under the original-register, previous-zero decode, block 2D0–2D8 loads and
right-shifts two values derived from R4, calling 1E9 for each. This explains
the input-dependent time observed in the [successor-byte wait](POLL-CALLER.md).
It does not establish a multiply, divide, or physical timing function.

Let S be R4 on entry and C the incoming carry-feedback bit. With zero shift
fill, the two calls to 1E9 begin with:

```
Q1 = ((S + C) modulo 256) >> 1
Q2 = S >> 1
```

2D0 loads S+C into Q. At 2D1, Q shifts its old value independently of the ALU
sum used for the RAM destination. Confusing these two values would give an
incorrect count at byte boundaries. After the first drain, 2D5 reloads S and
2D6 shifts Q again. The final branch at 2D8 transfers to 1CD.

Each call takes `bit_length(Q) + 1` iterations under the previous-zero policy:
it includes one iteration whose pre-shift Q is already zero. Zero starts
therefore still take one iteration. With N1 and N2 the two iteration counts,
the entire block, including called instructions and the final branch, takes:

```
11 + 2*(N1 + N2) microinstructions
```

In the tested local fixtures the block exits with Q=0, R0=0, unchanged R1–R15,
and a balanced stack. This description concerns persistent register effects.
ALU Y, flags, intermediate register values, and elapsed cycles do change;
an unidentified external consumer could make those changes significant.

## Verification

[The study](double_drain_study.py) runs all 256 R4 values with both possible
initial carry bits: 512 local executions using the real microinstructions and
existing condition policy. Other registers start with nonzero fixture values,
Q starts at A5, and external D is 55. Every run checks both drain inputs and
iteration counts, exact exit PC, all final registers, Q, and stack balance.
These are finite scenario checks, not proof for arbitrary condition or wiring
models. [Configuration](double-drain-study.json) makes the fixture explicit.

The preceding reset study sets S=255-X and enters this block with carry 1.
In its retained traces, 140 cycles precede the block and 19 follow it before
the first poll. Adding that fixed 159 to the local formula predicts all 256
first-poll cycles saved in the exhaustive caller report:

| Earlier external X | Q1 | Q2 | N1, N2 | Block cycles | First poll cycle |
| --- | ---: | ---: | --- | ---: | ---: |
| 00 | 0 | 127 | 1, 8 | 29 | 188 |
| 01 | 127 | 127 | 8, 8 | 43 | 202 |
| 7F | 64 | 64 | 8, 8 | 43 | 202 |
| 80 | 64 | 63 | 8, 7 | 41 | 200 |
| FF | 0 | 0 | 1, 1 | 15 | 174 |

All X values share this timing formula, although they do not share an identical
control path. The formula uses emulator instruction counts; no sample clock,
ADC event, or controller response time is identified.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/double_drain_study.py
```

[Report](results/double-drain-study/report.json) includes 512 local checks and
256 reset timing comparisons. Full local traces are retained for S=00 and FF
with both carry values. Unit tests check that trace extraction preserves the
entry Q and rejects a truncated drain.
