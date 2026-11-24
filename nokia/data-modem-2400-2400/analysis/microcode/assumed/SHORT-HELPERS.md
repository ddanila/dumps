# Six q3 short-helper contracts

*Runs under the [shared assumptions](ASSUMPTIONS.md).*

Six previously unnamed direct-call entries have distinct computational roles
under q3. Their retained RAM/Q effects and complete transient ALU-Y sequences
are checked separately. A transient value is not automatically a physical
write: this study assigns no output enable, port, or consumer.

## Retained state

| Helper | Direct caller used by local probe | Retained effect | Helper instructions |
| --- | --- | --- | --- |
| 04C–053 | 044 | R12=old R3; Q=0 | 8 |
| 09A–09D | 11C | R2=old R1; Q unchanged | 4 |
| 131–132 | 122 | All RAM/Q unchanged | 2 |
| 228–22A | 223 | All RAM/Q unchanged | 3 |
| 238–23F | 121 | R2=old R4; Q=old R0 | 8 |
| 240–247 | 123 | R2=old R4; Q=old R0 | 8 |

All other RAM is preserved. These instruction counts exclude the BSR caller.
04C uses the scenario's false selector 6 and executes 04D; the alternate skip
is outside this contract. Each local run starts at its actual caller with an
empty stack, pushes the real return address and pops it normally.

04C initially loads an external byte into Q. 050 later clears Q, and 051 copies
R3 into R12 using the zero carry from that clear. Thus the entry input has no
surviving RAM/Q effect, though it appears on the transient bus first.

09A first copies R0 into R2, then overwrites it with R1. That first copy is
visible on Y but not retained in R2. 131 exposes a sum and an AND without
writing registers. 228 exposes three different differences and returns.

## Complete transient sequences

Let a=old R0, q=old Q, d=the entry input byte, and `M(x)=x&255`.
All unmentioned external reads are 1. The following lists give Y in execution
order within each helper:

| Helper | Y sequence |
| --- | --- |
| 04C | `d, d, d&1, R3, 0, R3, M(2*R3), a&R3` |
| 09A | `a, R1, M(a+R5), a` |
| 131 | `M(R4+R12), a&R12` |
| 228 | `M(q-a-1), M(q-a), M(q-1)` |
| 238 | `0, M(a-1), M(a+(a!=0)), a, a, 0, R4, a` |
| 240 | `0, a, a, M(a-1), M(a+(a!=0)), 0, R4, a` |

In 238, the decrement at 239 uses the zero carry established by 238. Its carry
is one iff a is nonzero; 23A adds that carry to a. In 240 the same pair occurs
at 243–244, after the two unchanged-a outputs. Both then copy R4 and R0 into
R2 and Q. The operations can therefore be distinguished by their bus sequence
without a difference in final RAM/Q.

For a=1 and R4=7 the sequences are:

```
238: 0, 0, 2, 1, 1, 0, 7, 1
240: 0, 1, 1, 0, 2, 0, 7, 1
```

At a=0 the adjustment pair is FF,00; at a=FF it is FE,00. All arithmetic is
eight-bit. These observations do not establish a multi-byte sample format or
serial protocol; they constrain any future Y-consumer hypothesis.

## Validation

The study executes 65,536 local calls per helper, 393,216 total, comparing
complete final RAM/Q, instruction count and every helper Y value with the
independent formulas above. The two varied bytes are:

| Helper | Swept plane |
| --- | --- |
| 04C | R3 and entry D, with R0=R3; an additional test uses distinct R0/R3 |
| 09A | R0 and R1 |
| 131 | R0 and R12, with R4=R0 XOR A5 |
| 228 | R0 and Q |
| 238, 240 | R0 and R4 |

Other local state is declared in the runner; these planes are not an exhaustive
sweep of every register combination. Fourteen main-executor witnesses check
all local trace fields, including flags and actual stack slots. An unchanged
512-cycle handler-0 reset run reproduces its saved files byte for byte and
confirms that none of these helpers is reached: it waits in 127–12A before
the first call at 11C. All six helpers have local caller evidence here, not
new reset coverage. This is not claimed as terminal execution.

The mapping is q3 with previous flags, false selector 6 and the existing
zero-fill shift policy. Names describe supported computations, not presumed
multiply/filter functions. This removes six entries from the direct-call
interpretation queue while retaining the missing physical-consumer question.

[Configuration](short-helpers-study.json), [runner](short_helpers_study.py),
[report and traces](results/short-helpers-study/report.json).

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/short_helpers_study.py
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -p 'test_*.py'
```
