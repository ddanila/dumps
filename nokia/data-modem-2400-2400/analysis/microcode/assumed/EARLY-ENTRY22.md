# Early entry 022: shift selection and a skipped loop pop

*Runs under the [shared assumptions](ASSUMPTIONS.md).*

Under q3 and previous flags, early dispatch entry four reaches 022 with Q=FF.
It halves Q, then uses two external additions to decide whether to execute a
BLT immediately after a PLP. Skipping that BLT retains the frame. Executing it
pops the frame and continues. Both paths subsequently repeat at 05D with Q=7F.
No emulator stack repair is applied, and this result is not called a hardware
stack defect: the decode, conditions and entry association remain hypotheses.

## Shift selection and local contract

Let q be Q on entry, a=D022, x=D02B and y=D02C. The first addition at 022
produces carry c=(a+q>=256). 023 writes R1=(q-1+c)&255. Its carry is zero
exactly when q=0, independent of a. Thus the previous-carry branch at 024
selects:

- q nonzero: 025 shifts Q right, 026 clears R0, and 027 branches to 02B.
- q zero: 028 shifts an input sum left into R2, 029 writes zero into R0,
  and 02A branches to 02B. Q remains zero.

In either case Q at 02B is n=q>>1 and R0=0. The external byte used by 025
or 028 changes a temporary R2 value; 02F later overwrites it. The q=0 branch
is verified with local fixtures, because this reset entry supplies q=FF.
These local runs start at 022 with an empty stack and use real instructions;
they are not presented as reset reachability for 028–02A.

## The two-input carry boundary

02B pushes its loop address and exposes x+n. 02C adds y+n plus the previous
carry. Define:

```
c1 = int(x+n >= 256)
pop = (y+n+c1 >= 256)
```

02D shifts zero R0 right and performs TSK using the complement of 02C's carry.
When pop is false it skips 02E and leaves the PLP frame on the stack. When pop
is true it executes 02E. That BLT tests the zero result from 02D, so it falls
through to 02F while popping the frame; it does not repeat 02B.

The BLT itself also writes R0=(R1+n+1)&255. 02F copies that R0 into R2. When
the BLT was skipped, both remain zero. 030 exposes R4 and 031 branches to 05B.
The complete local state on reaching 05B is therefore:

```
Q = n
R1 = (q-1+int(a+q>=256))&255
R0 = R2 = (R1+n+1)&255 if pop else 0
all other RAM registers preserved
stack depth = 0 if pop else 1
instruction count = 13 if pop else 12
```

For zero-reset q=FF, n=7F. The threshold reduces to y>=129-int(x>=129).
The neighboring pairs x=128,y=128 and x=129,y=128 take opposite stack paths.
The distinction is caused by actual ALU carry feedback, not an imposed stack
policy. The local formulas cover arbitrary initial RAM, including the q=0
shift branch; they stop before the shared wait.

## Reset consequence

The first instruction at 022 executes at cycle 18. The first 05D cycle is
32 when the BLT was skipped and 33 when it executed. With z=D05B, the stable
state inside the later wait is:

```
Q=127; R0=128; R1=254+int(a!=0); R4=(127+z)&255
all other RAM registers zero
```

The different temporary R0/R2 values from 02E/02F are overwritten there.
Since R3=0 and Q=127, the previous-zero comparison cannot return under these
fixed inputs. The complete modeled state repeats every seven instructions.

Maximum stack depth is two if the earlier PLP frame was retained, otherwise
one. The current 05D frame is pushed and popped on every pass; the older
frame persists beneath it in the skip case. This explains the depth difference
observed in [EARLY-WAIT.md](EARLY-WAIT.md) without concealing it or treating a
clean bounded run as proof of physical hardware correctness.

## Verification

Two arithmetic planes check 131,072 cases: every q/a pair for the preparation
and shift-selection predicate, and every x/y pair with reset n=127 for the
pop/skip predicate. The study then runs 1,024 complete 192-instruction reset
cases, covering all x values and four y values around the carry boundary.
Other inputs vary with those values; independent randomized regressions vary
all bytes separately.

Four saved reset witnesses straddle the threshold. Four separate local
witnesses exercise q=0,1,128,255 and verify all RAM/Q, actual branch targets,
stack depth and arrival at 05B. Additional randomized local fixtures cover
both paths with independently chosen registers. All saved witnesses replay
byte for byte. No physical consumer is assigned to the transient arithmetic.

[Configuration](early-entry22.json), [runner](early_entry22.py), and
[report](results/early-entry22/report.json).

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/early_entry22.py
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -p 'test_*.py'
```
