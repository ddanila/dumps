# The 30B helper distinguishes retained source mappings

The retained mappings give two different interpretations of 30B–310 under
original register roles. q1–q4 clear Q before the loop; fitted_original masks
Q with R0 and then drains it. Both return with R0=Q=0, but the value retained
in R5 and the loop duration differ. This is a candidate discriminator, not a
reason by itself to promote one mapping as physical wiring.

The [study](masked_drain_study.py) uses the actual call at 304 and stops on
return to 305. It shares the existing previous-flag/defined-carry policy and
zero shift fill. The q1–q4 instruction, register, carry and sequencer fields
are checked identical over all six helper words. q2 therefore represents
that group in the dynamic comparisons. The fitted_swapped register layout
is outside this comparison; it must not inherit these register formulas.

## Exact state changes

Let A be initial R0 and q be initial Q. All byte additions below wrap before
shifting. All RAM other than R0 and R5 is preserved.

| Property | q1–q4 | fitted_original |
| --- | --- | --- |
| Q after 30B | `(D+q) mod 256` | q |
| Q after 30C | 0 | `m=A AND q` |
| Final R5 | `((A+1) mod 256) >> 1` | `((A+m+1) mod 256) >> 1` |
| Final R0, Q | Both zero | Both zero |
| Loop iterations | Always 1 | 1–5, according to m |
| Instructions including call and return | 7 | 7–15 |

In q1–q4, 30B samples D into Q, but 30C immediately computes zero AND R0 and
replaces Q with zero. This removes the input's effect from the helper's final
internal state. It does not prove the board ignores the transient value: a
physical external consumer is not identified.

In fitted_original, 30B preserves Q and 30C computes R0 AND Q. No helper
instruction selects D under this mapping. 30D adds A+m+1, stores the shifted
low byte in R5, and shifts Q once. Each subsequent 30E/30F iteration shifts
Q twice. The branch at 30F uses the preceding 30E zero flag, which describes
Q **before** that instruction's shift. Consequently a final iteration with
zero on entry is required.

The exact iteration count is `1 + ceil(bit_length(m >> 1) / 2)`, giving:

| Masked value m, hexadecimal | Iterations |
| --- | --- |
| 00–01 | 1 |
| 02–07 | 2 |
| 08–1F | 3 |
| 20–7F | 4 |
| 80–FF | 5 |

For A=FF and q=FF, q1–q4 leave R5=00 after one iteration; fitted_original
leaves R5=7F after five. Looking only at final R0/Q would miss the difference.
Across all A/q pairs, the final R5 values differ in **56,788 of 65,536 cases**.

## Verification

There are **135,168 local comparisons**, with complete RAM/Q, cycle and
iteration counts checked against independent arithmetic formulas:

- All 65,536 A/q combinations under each of the two interpretations.
- All 256 D values at eight selected A/q fixtures under each interpretation.

For fitted_original, the exhaustive A/q sweep gives 8,748 one-iteration,
6,804 two-iteration, 12,096 three-iteration, 21,504 four-iteration and 16,384
five-iteration cases. All q1–q4 representative cases take one iteration.
Nineteen integrated witnesses match the component probe instruction by
instruction, including ALU results, flags, branch decisions and Q. The real
sequencer stack balances in every local probe.

These are local calls with explicitly supplied RAM/Q; they do not establish
which nonzero operands the full program supplies from reset. They also do not
identify a filter, multiplier, output channel or physical timing operation.
A cleared input and constant loop count may reflect an incorrect source
mapping, or external effects outside the current model. The differing R5
values and durations are recorded as constraints for caller and wiring work.
No default mapping or scenario changes.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/masked_drain_study.py
```

[Configuration](masked-drain-study.json) records the fixtures and shared
condition policy. The [report](results/masked-drain-study/report.json) contains
counts, full witnesses, an exhaustive-comparison digest, and source/trace
hashes. Historical mapping-specific annotations remain separate.
