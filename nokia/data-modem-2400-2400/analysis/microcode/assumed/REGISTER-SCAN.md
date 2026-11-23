# The 302 branch reaches a register-difference scan

Under q2 and fitted_original, 319–334 writes neither RAM nor Q and selects
no external D operand. Its loops repeatedly expose register differences on
the ALU output. With the existing condition scenario, the first two loops
execute once; the final loop repeats exactly when R15 is greater than or
equal to R0. This explains the path actually selected at 302, rather than the
[local double-drain caller](DRAIN-PREFIX.md) that the same scenario bypasses.

## What the three loops compute

Every instruction in the following groups computes `Rb−R0 mod 256`, with
carry set when `Rb>=R0`. The difference is exposed as ALU F/Y but not stored.

| Loop | Registers used as Rb, in order | Loop test in the shared scenario |
| --- | --- | --- |
| 31A–324 | R1 through R11 | Select 6, constant zero: exit |
| 326–329 | R0, R13, R14, R15 | Select 6, constant zero: exit |
| 32C–32E | R13, R15, R3 | Select 2, preceding carry: repeat if R15>=R0 |

The first two groups do not form a complete sequential dump of all sixteen
registers: R12 is absent, and 326 compares R0 with itself. No physical register
readout interface, output latch or consumer has been identified, so these
are transient ALU results rather than claimed board writes.

At 32E, the comparison being computed is R3−R0, but the branch consumes the
preceding carry from 32D's R15−R0. Equality therefore repeats. RAM, Q and both
comparison operands remain fixed, so a failed test cannot converge under the
selected assumptions. The repeated complete state has period three instructions.
External D changes alone cannot release it because none of these words selects D.

The surrounding no-load instructions also produce transient results. Some of
those differ between the two mappings; identical scan comparisons and control
flow do not imply that every ALU output in 319–334 is identical. A physical
consumer or a different condition source could change the interpretation.

## Exhaustive local boundary check

The [study](register_scan_study.py) executes all 65,536 R0/R15 pairs under each
mapping, with the other RAM registers and Q explicitly supplied. It checks the
predicted difference and carry at every scan instruction, the complete final
RAM/Q state, and the return or repetition:

| R0/R15 relation | Cases per mapping | Outcome from entry 319 |
| --- | --- | --- |
| R15<R0 | 32,640 | Reach 07B after 28 instructions |
| R15>=R0 | 32,896 | Exact period-three cycle at 32C–32E |

The repetition check includes full stack contents, stack pointer, ALU flags
and previous carry. It observes two complete iterations after the last loop's
entry, rather than treating a timeout as proof of a cycle. The helper has no
RAM/Q destinations under either decode; this is also checked statically for
all 28 words. Nonzero local Q and unrelated RAM values remain unchanged.

## The values supplied by reset

Another **512 integrated runs** start at reset with global dispatch index 3,
all 256 default external bytes, and diagnostic zero replies at the early waits.
Every run reaches 302 and takes its select-5 branch to 319. None reaches 304
or the 30B helper on this path.

| Mapping | R0 on entry to 319 | R15 | Outcome |
| --- | --- | --- | --- |
| q2 | FF | 00 | All 256 inputs leave the scan and reach terminal 084 |
| fitted_original | `FF−D` | 00 | D=00–FE reach 084; D=FF repeats the final scan |

At D=FF under fitted_original, R0=R15=0 makes the final comparison carry set.
This is a concrete reset-reachable instance of the local repetition rule.
Every scan instruction preserves the recorded entry RAM/Q state in these
runs. These outcomes still depend on the scenario's select-5 and select-6
constants, previous-carry timing, and the retained mappings; they are not a
claim about physical modem completion or a hardware hang.

## Reproducibility

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/register_scan_study.py
```

[Configuration](register-scan-study.json) fixes the mapping paths and input
assumptions. The [report](results/register-scan-study/report.json) includes all
reset entry states, local boundary witnesses, counts, comparison digest and
source/trace hashes. Representative local traces are compared instruction by
instruction with the integrated runner. Eight complete reset witnesses cover
D=00,01,FE,FF for both mappings. Default mappings and scenarios remain unchanged.
