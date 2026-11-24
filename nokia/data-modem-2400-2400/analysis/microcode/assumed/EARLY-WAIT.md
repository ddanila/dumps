# Early dispatch and the fixed-register wait at 05D

The alternative boot branch (selector 5 false at 003) reaches an eight-entry
computed table at 008. Under q3 and previous flags, seven tested entries settle
into the fixed-register wait at 05D–063; entry five clears Q and reaches 084.
The wait is not an external-byte poll under this decode: its only D-dependent
instruction exposes an arithmetic result without changing retained state.

## Reset prefix and table premise

From zero reset, 000 copies R0 to R2, 001 exposes an input sum, and 002 loads
an independent byte a into Q. With selector 5 false, 003 falls through to the
real call at 004. The existing 06F helper leaves R0=FF and adds the independent
D076 byte b to Q. 005–007 expose arithmetic and copy zero R1 into R2.
008 then overwrites Q with R0=FF before dispatching. Thus the two earlier input
bytes do not survive in Q on any of these paths.

This experiment explicitly chooses `index_source=scenario` at 008. The target
list is the existing Am27S31-associated hypothesis, not a newly recovered
hardware index source. Other dispatches retain the same global scenario index.

| Index | Actual target | Q at wait | First 05D cycle | Other retained values while waiting |
| --- | --- | ---: | ---: | --- |
| 0 | 009 | FF | 24 | none |
| 1 | 00F | FF | 24 | none |
| 2 | 00B | FF | 22 | none |
| 3 | 013 | 01 | 38 | R14=FD |
| 4 | 022 | 7F | 32 | R1=FF |
| 5 | 00D | 00 | 26 | returns on first pass |
| 6 | 032 | 01 | 30 | none |
| 7 | 054 | FF | 25 | R15=FF |

Numbers except cycle counts and indices are hexadecimal. Each row reaches
the wait with R3=0. During a repeating pass, R0=(Q+1)&FF, R2=0 and
R4=(D05B+Q)&FF; registers not mentioned are zero. These are complete reset
outcomes for the supplied inputs, not general interpretations of every branch
inside each target body. The longer 013/022/032 bodies remain separately open.

The 022 route skips its BLT at 02E after pushing at 02B. It carries that loop
frame into 05D, so maximum stack depth is two; the other routes peak at one.
No stack repair is applied. A bounded wait may end with its current PLP frame
pushed or popped, depending on where the trace stops.

## Short entries and the completing route

009's initial branch is false in this context; 00A does not skip, and 00B/00C
lead to 05B. Direct entry at 00B shares that suffix. Entry at 00F copies the
negation of zero R7 into R3, loads a temporary input sum into R2 at 010 and
branches from 012 to 05B; the temporary R2 is overwritten in the wait.

Entry at **00D** differs because it first loads Q from zero R2. 00E and 00F
leave R3 zero, so this route reaches 05D with Q=R3=0 and returns immediately.
Entry at 054 instead retains Q=FF. 055 writes FF to R15, the false carry test
at 056 allows 057, and 058 joins 05B. Entry 013 reaches 059, where Q is reloaded
from the default D=1 before joining 05B through 05A.

05B stores the external byte plus Q into R4, and 05C enters the loop. On the
returning route, let x=D05B and y=D064. The complete terminal state is:

```
Q = 0
R0 = R2 = 1
R3 = (y-1)&255
R4 = x
all other RAM registers = 0
```

064 performs the byte subtraction with carry input zero. 065 and 06A copy R0
to R2; 066–06D otherwise expose transient arithmetic without retained writes.
06E branches to 084. The first 084 cycle is 44, with final stack depth zero.
Neither an analog output consumer nor a physical completion signal is inferred.

## Exact loop predicates

One pass consists of seven actual instructions:

- 05D pushes the loop address and sets R0=(Q+1)&FF.
- 05E preserves R2; 05F and 061 copy R3 into R2.
- 060 exposes D+Q, with no retained write.
- 062 exposes Q−R3 modulo 256 with carry input one.
- 063 exposes Q+R3 modulo 256 and performs BLT.

Q and R3 do not change. Previous-zero timing returns exactly when Q=R3;
current-zero timing returns exactly when Q+R3=0 modulo 256. Either predicate
holds for 256 of the 65,536 Q/R3 pairs. Otherwise, once the two register copies
have settled, another pass repeats the same state under constant future inputs.
Changing D060 cannot change the retained state or either predicate: 062 and
063 both use mapped carry inputs, discarding 060's carry before the test.

This is a mapping constraint, not evidence that physical hardware waits forever.
It also explains why naming this code an external acknowledgment poll would be
misleading under the current q3 hypothesis.

## Evidence

The local check evaluates all 65,536 Q/R3 pairs with nonzero register fixtures,
checks every retained register and both flag predicates, and varies D060 with
the pair. Main-executor regressions exercise both timings, matching and failing
pairs, and actual PLP/BLT stack behavior.

The reset study executes 2,048 full 256-instruction runs: eight entries and
four boundary values each for D002, D076, D05B and D064. It checks complete
final RAM/Q, table targets, wait-entry timing, terminal timing or exact
seven-instruction state recurrence. Eight saved witnesses cover every entry.
Independent random reset cases break the boundary sweep's limited input set.

[Configuration](early-wait.json), [runner](early_wait.py), and
[report](results/early-wait/report.json).

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/early_wait.py
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -p 'test_*.py'
```
