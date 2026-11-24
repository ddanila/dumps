# Idempotent mask tests at 127 and 12C

*Runs under the [shared assumptions](ASSUMPTIONS.md).*

The fitted-original decode interprets loops 127–12A and 12C–12F as identical
mask tests. They contain no external-D operand and no changing counter. Under
the selected previous-flag policy, a failed first test cannot become successful
on a later pass without an effect absent from this model.

## Exact local operation

Each pass copies R1 to R2, then sets `Q = Q AND R0`. The following subtraction
computes `Q−R0 mod 256`, without storing it. The AND instruction uses carry
input one; under the explicitly selected defined logical-carry model its carry
output is one, which supplies the subtraction's carry input.

Previous-flag BLT therefore exits exactly when `(initial_Q AND R0) == R0`:
every bit set in the R0 mask must already be present in Q. Otherwise the loop
repeats. AND with a fixed mask is idempotent, so further passes do not change Q.
All register RAM except the copied R2 remains unchanged.

The enclosing helper 126–12B adds R10 to Q before the loop and again on its
return. Thus the containment predicate applies to `(initial_Q+R10) mod 256`,
and a returning helper produces `(masked_Q+R10) mod 256`. Helper 12C–130 has
neither addition and returns the masked Q directly.

Current-flag timing instead tests the BLT instruction's ALU result:
`(masked_Q + int(masked_Q == R0)) mod 256`. Exit requires this to be zero.
This is a distinct predicate, not a minor change in iteration count. Neither
alternative is promoted to recovered condition wiring.

## Exhaustive local verification

The [study](mask_loop_study.py) starts at the actual calls 11B and 11D, using
nonzero initial register fixtures and every R0/Q byte pair under both timings.
All **262,144 comparisons** match the independent predicates and final RAM/Q.

| Timing | Returns per helper | Exact repeated states per helper |
| --- | ---: | ---: |
| Previous flag | 6,561 | 58,975 |
| Current flag | 6,306 | 59,230 |

Each row covers 65,536 input pairs for each of the two helpers. The previous
return count is also 3^8: per bit, the allowed (mask,Q) combinations are 00,
01, and 11. The pre-add in helper 126 is a permutation of all Q bytes and
therefore preserves that count.

Every non-returning case repeats the complete local machine state at the
loop header with period four instructions. Sixteen representative cases also
replay in the ordinary integrated executor, checking PC, all RAM and Q. The
probe does not repair stack state or force loop conditions.

## Reset-path consequence

The [current-Y dispatch scenario](DISPATCH109.md) chooses entry zero when
D=07,0F,...,FF. Replaying those 32 reset paths establishes R0=255−D, last written
by 074, with Q=0 and R10=0 at entry 126. The subtraction then produces D+1
modulo 256. Consequently only D=FF exits under previous-flag timing; the other
31 inputs repeat. Three witnesses retain complete 256-cycle reset traces.

This explains the loop outcomes in the dispatch study. Unlike the earlier
D-dependent shift loops, varying the external-read stub while execution remains
inside this loop cannot release it: decoded source fields select only internal
registers or constants throughout both helpers. The source-field check is
performed for every instruction, rather than inferred from a constant-input
run.

## Interpretation limit

This is a concrete constraint on the candidate mapping and condition policy.
It does not prove that real hardware waits forever. A different condition
source, field assignment, or modeled interaction could invalidate the local
interpretation. Conversely, the current model cannot explain the repeated
passes as a changing external-byte poll or a multiply/countdown loop. The
caller precondition is satisfied by the D=FF reset case but not the other 31
cases in this optional dispatch scenario.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/mask_loop_study.py
```

[Configuration](mask-loop-study.json) records the supplied register fixture and
reset inputs. The [report](results/mask-loop-study/report.json) contains counts,
predictions, local and reset witnesses, and source/execution hashes. Default
mappings and scenarios are unchanged.
