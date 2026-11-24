# Independent captured bytes reach the paired-arithmetic loop

Under q2, two separately supplied bytes can be followed from zero reset into
a 16-bit operand at 389–3A1. The addition path returns when the **high byte**
of its result is zero, even when the low byte is nonzero. This gives a concrete
counterexample to interpreting its exit as a whole-word zero test.

The earlier [preceding-Y experiment](Q2-DISPATCH.md) used the same external
byte at both capture sites. That constrained the captured word to repeated
bytes, hiding most of this exit boundary. This experiment changes the input
stubs, leaving the mapping, previous-flag policy and instruction execution
unchanged. It does not establish a physical channel, protocol or DAC write.

## End-to-end data path

All runs begin at 000 with zero RAM and Q. The diagnostic input schedule is:

| Read site | Supplied bytes | Purpose under q2 |
| --- | --- | --- |
| 117, 106 | 1, then 0, holding 0 | Release the two carry-qualified waits |
| 118 | `(low+1) mod 256` | Capture `low` in R6 because R0=FF |
| 107 | `(high+1) mod 256` | Capture `high` in R7 because R0=FF |
| 38E | Independent selector 0–3 | Previous Y supplies the index at 38F; R14=0 |
| 36D | 0 | Release the later carry-controlled loop |
| Other sites | 1 | Retain the existing constant diagnostic input |

The scenario retains top-level dispatch index 5 and overrides only 38F with
preceding-Y indexing. The instructions at 38C/38D copy R6/R7 into R10/R11.
Thus both second-pair operands equal `V = low + 256*high`. The first-pair
operands R4/R5 and R8/R9 are zero in these reset runs. The four table entries
expose these ALU/Y byte results without storing them:

| Entry | Addresses | First 16-bit result | Second 16-bit result |
| --- | --- | --- | --- |
| 0 | 392–395 | 0+0 | `2*V mod 65536` |
| 1 | 396–399 | 0−0 | `2*V mod 65536` |
| 2 | 39A–39D | 0−0 | `V−V = 0` |
| 3 | 39E–3A1 | 0+0 | `V−V = 0` |

The verifier compares each executed low/high result against independent
16-bit arithmetic, checks the capture and copy states, and checks that the
table preserves RAM and Q. This experiment does not exercise independent
nonzero operands in the first pair or unequal operands in the second pair.

## The exit observes only the final high byte

BLT at 390 uses the preceding zero flag with inverted polarity. Its test is
false when the last high byte is zero; it consumes the loop frame and falls
to POP at 391, returning normally to 347. Otherwise it repeats from 389.
For addition, the high byte of `2*V mod 65536` is zero exactly for:

- `V = 0000–007F`, or
- `V = 8000–807F`.

Only 0000 and 8000 in these intervals produce a zero *whole* result.
For example, reset-captured V=0001 gives low/high output **02/00** and still
returns. V=0080 gives **00/01** and repeats. V=8001 also gives **02/00** and
returns after 16-bit wraparound. Subtraction of the copied pair returns for
all tested values.

The independent capture values survive in R6/R7 and R10/R11 through the
continuation. The zero reply at 36D permits the returning cases to reach 084;
there is no injected return, PC change, stack repair or initialized data
register. This downstream reply is a separate explicit assumption, not a
recovered response from another board.

## Bounded sweep and limitations

The sweep covers every low byte, high bytes 00, 01, 80 and FF, and all four
entries: **4,096 clean reset runs**, 192 cycles each.

| Entries | Terminal 084 | Repeating paired loop |
| --- | --- | --- |
| 0 | 256 | 768 |
| 1 | 256 | 768 |
| 2 | 1,024 | 0 |
| 3 | 1,024 | 0 |

Of the 2,560 terminal runs, **508 return with a nonzero second-pair low-byte
result**. The 1,536 nonterminal cases repeat the table wrapper every 12 cycles.
All runs avoid unused words and stack errors. Seven complete witnesses retain
the boundary cases and both subtraction entries. This is a sweep of four
high-byte slices, not an exhaustive reset sweep of all 65,536 input words;
the full interval formula follows from the stated 16-bit arithmetic.

The result supports the narrower routine description “paired arithmetic with
a final-high-byte exit.” Calling it a full-word comparison, a finished DSP
operation, or a physical output protocol would require additional evidence.
The output bytes remain transient ALU/Y values; no new external-write rule is
introduced. No coverage or annotation-count increase is claimed.

## Reproduce

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/paired_capture_study.py
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -p 'test_*.py'
```

[Configuration](paired-capture-study.json) records the diagnostic assumptions.
The [report](results/paired-capture-study/report.json) records every run's
input, expected result, outcome, trace/scenario digests and maximum stack
depth, plus detailed capture/output events for the witnesses and source hashes.
