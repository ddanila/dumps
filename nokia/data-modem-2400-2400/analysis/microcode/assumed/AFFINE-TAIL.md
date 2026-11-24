# Saving R0, optionally loading Q, and forming a byte sum

*Runs under the [shared assumptions](ASSUMPTIONS.md).*

Under q1, q2 and q4, the helper at 28E–295 saves old R0 in R3, optionally
loads Q into R0, and leaves `(R0 + 2*R1 + 1) mod 256` in R15. Q and all
other registers are preserved. Five q2 reset witnesses connect this operation
to the value produced by the [nested ROM routine](NESTED-RESET.md).

## Instruction-level interpretation

Let `old0` be R0 on entry and `q` be Q. The actual call at 213 pushes a return
to 214; its ALU operation does not change RAM or Q. The helper then executes:

| Address | Stored effect or control |
| --- | --- |
| 28E | R3 = old0 |
| 28F | R15 = R1 |
| 290 | Skip 291 if condition select 6 is true; ALU output is zero |
| 291 | R0 = q; carry becomes 1 |
| 292 | R15 = R2 if 291 ran, otherwise R2−1; uses the preceding carry |
| 293 | R15 = R1, overwriting the temporary value from 292 |
| 294 | R15 = R0 + R1, modulo 256 |
| 295 | R15 = R1 + R15 + 1, modulo 256; return to 214 |

Thus the two complete outcomes are:

| Select-6 test at 290 | R0 on return | R3 on return | R15 on return |
| --- | --- | --- | --- |
| False, execute 291 | q | old0 | `(q + 2*R1 + 1) mod 256` |
| True, skip 291 | old0 | old0 | `(old0 + 2*R1 + 1) mod 256` |

The carry from 294 is not fed into 295: its mapped carry-in is explicitly
one. This is a modulo-256 byte expression, not a proven multi-byte addition.
No instruction in this helper selects external D under these three profiles.
The other retained mappings differ at some of these instructions and are
outside this annotation's scope.

## Both skip outcomes checked with real calls

The local experiment routes select 6 to an explicit external condition stub
and tests both values. The retained reset scenario instead fixes that selector
false. No physical source for select 6 is recovered here.

For each of q1/q2/q4 and both outcomes, the experiment checks all 65,536 Q/R1
pairs. Initial R0 is `(73*Q+17*R1) mod 256`, R2 is `Q XOR R1 XOR A5`, and the
remaining registers use fixed nonzero fixtures. Because 73 is odd, each fixed
R1 also sees every initial R0. The sweep therefore exhausts the controlling
Q/R1 pair on the load path and old-R0/R1 pair on the skip path, while not
claiming exhaustive combinations of all sixteen registers.

All **393,216 local calls** match the independent final-RAM formula, preserve
Q and the other registers, and return with the single caller frame consumed.
The load path takes nine instructions including the call; the skip path takes
eight. The temporary 292 result is checked separately so its carry dependence
is not hidden by the subsequent overwrite. Twelve complete integrated
witnesses match the local model's PCs, next PCs, ALU results and tests exactly.

Examples include Q=FF/R1=00, which produces R15=00 on the load path, and
Q=00/R1=FF, which produces R15=FF. An explicit skip retains old R0 and changes
the corresponding result as predicted.

## Data flow from reset into the terminal tail

All five nested reset cases are replayed under their original mappings,
inputs and seeds. Their full trace digests match the earlier results. Each
reaches the helper with R0=R1=0 and select 6 false:

| Reset seed | Q on entry | R0 on return | R15 on return |
| --- | --- | --- | --- |
| 115 | CC | CC | CD |
| 501 | DE | DE | DF |
| 2855 | 20 | 20 | 21 |
| 3519 | 00 | 00 | 01 |
| 3614 | 8F | 8F | 90 |

R3 becomes zero in all five, including seed 2855 where its previous value was
FF. The earliest subsequent selection of the returned R0 is instruction 216.
It computes `XNOR(R0,Q)`. Since the helper established R0=Q, the result is FF
with zero flag clear. The unconditional branch goes to 078, whose test uses
that previous zero flag and falls to 079. Instruction 078 itself produces
zero; 079's inverted previous-zero test is consequently also false, falling
to 07A. These executed tests connect the saved arithmetic state to the
terminal path.

The trace audit tracks each returned R0/R3/R15 until its first later ALU
operand selection, direct A-to-Y selection, or overwrite. Selection is a
syntactic data path observation, not proof that the operand influences the
result—for example, zero AND a register ignores its value.

R15 is not selected as a register source in these five continuations. In
seeds 115 and 2855, instruction 099 overwrites it before it is selected; the
other three traces retain it through terminal 084. R3 is neither selected nor
overwritten after this helper within these traces. These observations do not
rule out external capture of Y at the arithmetic instructions or a later
hardware restart. The physical output enable, destination and timing remain
unresolved, so the affine result is not assigned a modem-level purpose.

## Reproduction

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/affine_tail_study.py
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -p 'test_*.py'
```

[Configuration](affine-tail-study.json), [script](affine_tail_study.py), and
[report](results/affine-tail-study/report.json) retain the scoped assumptions,
execution digest, twelve local witnesses, five reset traces, register-use
observations and source hashes. The listing labels only q1/q2/q4 for these
eight newly interpreted words.
