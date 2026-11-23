# Disconnected entry families and a conditional one-unit adjustment

The 22 unresolved words form seven entry families under the current control
flow. Two roots cannot be supplied by an unchanged Am27S31 byte plus a bank:
the complete 512-byte ROM contains neither 56 nor BD. This rules out simply
finding a different ROM offset for entries 256 and 3BD under that address
construction. It does not rule out arithmetic on the ROM output, a different
source, or a different instruction decoding.

The same investigation identifies a tentative arithmetic role for the paired
tails at 2D9 and 2DC: they differ by one in their first ALU result and then
produce identical remaining results, without changing RAM or Q. This holds
across all four retained Q-independent datapath layouts in the local tests.
The [state-convergence follow-up](TAIL-CONVERGENCE.md) shows that the difference
is transient: the two paths have equal modeled state at their 07B join. An
external consumer or different decoding would be needed for a lasting effect.

## Entry families

Starting from the [999-word graph](LOCAL-CASES.md), the study probes each of the
22 disconnected words with an empty stack and with one return sentinel. The
seven roots below have no predecessor within that disconnected set. Root
families can overlap; 0FD and 256 both reach 2D9. These are local diagnostics,
not newly established paths from reset.

| Root | Disconnected words reached locally | Stack role | ROM offsets containing its low byte |
| --- | --- | --- | --- |
| 0FA | 0FA | Safe without caller; no return | 067, 07B, 174, 1E3 |
| 0FD | 0FD–0FF, 2D9–2DB | Safe without caller; no return | 1C1–1C3, 1E6 |
| 256 | 256–257, 2D9–2DE | Safe without caller; no return | None |
| 258 | 258 | Safe without caller; a caller frame permits downstream overflow | 03E, 11F |
| 2CF | 2CF | Safe without caller; no return | 009, 00F |
| 2DF | 2DF | Requires caller; returns through 2FF | 05F |
| 3BD | 3BD–3BF, 287–28A | Safe without caller; no return | None |

The table lists only the disconnected part of each local traversal. Most paths
also enter already reachable code. Adding a return frame at 258 exposes
possible overflows at 223 and 2C4. Entering 2DF without a frame instead exposes
underflow at 2FF. Thus these roots cannot all be treated as interchangeable
computed-call entries.

A byte match is weak evidence by itself. For example, CF occurs at 009 and
00F inside the known full sine period. Reinterpreting those samples as dispatch
targets would require independent evidence of index selection and bank bits.
No targets or reset scenarios are changed by this study. All 22 words remain
unresolved, rather than being relabelled as explained exceptions.

## Conditional adjustment tails

At 256, a conditional branch selects 2D9. Otherwise 257 branches to 2DC.
Both tails contain three words and finish with a branch to 07B:

| Candidate layouts | Y at 2D9 | Y at 2DC |
| --- | --- | --- |
| 1, 3, 4 | R12 − R0 − 1 | R12 − R0 |
| 2 | R12 − 1 | R12 |

Arithmetic is modulo 256. The first words differ only in bit 10.4, the mapped
carry-in bit under these hypotheses. Their carry-feedback selector is clear,
so this difference is independent of the incoming carry. The next two ALU
results are equal between the tails within each layout; their formulas differ
between layouts. All six words decode as no-load destinations. RAM and Q are
preserved, while Y and flags are computed.

For a concrete fixture with R0=55, R12=00, R15=5A, Q=A5 (hex), the three Y
values are:

| Layout | 2D9 path | 2DC path |
| --- | --- | --- |
| 1 | AA, AF, 5A | AB, AF, 5A |
| 2 | FF, 5A, 0F | 00, 5A, 0F |
| 3 | AA, AF, 0F | AB, AF, 0F |
| 4 | AA, 5A, 0F | AB, 5A, 0F |

The sweep tests every R12 byte, five R0 values, two Q values, two external D
values, and both initial carries. R15 is set to R12 XOR 5A, with the remaining
registers initialized to a fixed nonzero pattern. That gives 10,240 paired
fixtures per layout, 40,960 total, and zero violations of the one-unit
difference, equal subsequent outputs, or preserved RAM/Q properties.
This is not an exhaustive sweep of all register combinations.

“Conditional one-unit adjustment tail” is therefore a useful provisional
routine label. No output strobe or downstream consumer of the first Y value
has been identified. It is not yet evidence of rounding, DAC output, or a
specific modem algorithm. The meaning of condition select 2 at 256 remains
unknown, and this local test does not choose that condition automatically.

## Reproduce

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/fragment_study.py \
  --out /tmp/nokia-fragments
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -p 'test_*.py'
```

[Configuration](fragment-search.json) and [report](results/fragment-study/report.json)
preserve ROM matches, local stack exceptions, decoded tails and numerical
examples. The report reproduces byte for byte; all 60 functional/assumption
tests pass, including nonzero and wraparound tail fixtures. The full plan
remains incomplete.
