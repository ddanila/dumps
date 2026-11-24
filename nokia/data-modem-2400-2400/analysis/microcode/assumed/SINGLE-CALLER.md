# Preparation data survives the alternate 18B caller

*Runs under the [shared assumptions](ASSUMPTIONS.md).*

Unlike the three-call path at 133, the alternate caller at 18B can preserve
preparation-input effects through the subsequent routines. Swapped register
roles retain an effect in R10 or R12. Some original-role source candidates
instead retain it in Q, and one also in R2. Thus data survival alone does not
choose the register assignment.

These are conditional model results, not identified hardware transfers or
proof of a modem algorithm. The paths are local fixtures and stop before 195.

A [first-use follow-up](FIRST-USE.md) now identifies which surviving values
are read before replacement and traces two preparation-dependent arithmetic
results beyond 195.

## What ran

[single-caller-search.json](single-caller-search.json) supplies the assumptions.
Execution starts at 18B with empty stack and zero RAM, calls 341, calls 3EA
through 18C, then executes the actual caller and callees through 194. This
includes calls to 270, 238 and 240. The single transform wrapper exits after
one iteration. Its four table entries are all tested.

Three condition decisions inside 270 (272,278,27D) vary independently across
all eight bit masks. Mask bit 0 controls 272, bit 1 controls 278, and bit 2
controls 27D. Initial Q is 00 or 55. D is zero outside 341–344. Each input
comparison changes one of those four D bytes from zero to 01 or 80.

Only the four retained candidates that select D,Q in preparation are tested:
07,23,27,31. The other twelve retained layouts ignore the D bytes at these
instructions. Both original and swapped A/B roles are tested. This makes 64
mapping/role/condition profiles, each with eight entry/Q combinations and
nine input runs, or 4,608 primary local runs. Sixteen extra runs save marked
versus zero traces. All finish with balanced stack in 51–55 instructions,
maximum stack depth three. No results count toward reset coverage.

## Results at 195

Each profile compares 16 perturbations per input byte: four entries × two
initial Q values × two perturbation values.

| Register roles | Candidate/conditions | Surviving tested preparation effect |
| --- | --- | --- |
| Swapped | All four candidates, all eight masks | Third D byte affects R10 in 8 comparisons and R12 in 8; no Q or checkpoint-Y difference |
| Original | 23 and 27, masks 6 and 7 | Third/fourth D bytes affect Q in 12/16 comparisons respectively |
| Original | 31, masks 6 and 7 | Same Q effect, also present in R2 |
| Original | Other tested profiles | No final RAM, Q or checkpoint-Y difference |

The first two preparation bytes show no final checkpoint effect in these
comparisons. With swapped roles, the fourth byte also loses its effect before
195. These finite perturbation results do not establish independence for all
input combinations or initial machine states.

The original-role survivors require the branch at 278 to be taken and TSK
at 27D to skip the instruction at 27E. The choice at 272 does not distinguish
masks 6 and 7 for this result. This identifies a concrete path to inspect,
rather than attributing survival simply to register role.

## Two marked-input witnesses

With candidate 07, swapped roles, Q=00, entry 0, mask 0, and D bytes
12,34,56,78 (all values below hexadecimal):

| Checkpoint | R10 R11 R12 R13 |
| --- | --- |
| 18C, after preparation | EE CB AA 87 |
| 18D, after transform | AA 87 00 00 |
| 18F, after 270 | AA 87 00 00 |
| 190, after 238 | AA 87 00 00 |
| 193, after 240 | AA 87 00 00 |
| 195, before the branch | AA 00 00 00 |

The final R10 differs from the zero-input trace. In contrast, candidate 31
with original roles, Q=00, entry 0 and mask 7 finishes with Q=87 and R2=87;
the corresponding zero-input trace has both zero. These witnesses preserve
different internal representations of preparation data. Neither demonstrates
what consumes those values after 195.

## Implications and limits

The earlier three-call result does not generalize to this caller. It also
would be premature to prefer swapped roles because their survival is less
condition-dependent: the actual conditions, indices and external reads are
unknown, and the swapped roles conflict with the previous forward-transform
interpretation. The original-role alternatives now have an explicit surviving
input path that was absent from the small reset-run samples.

Next evidence should come from downstream use of Q/R2 versus R10/R12 beyond
195, and from the condition and external-input assumptions that select those
paths. Physical memory writes, ADC/DAC activity and controller traffic remain
unidentified. Intermediate ALU outputs could have external consumers that
this internal-state comparison does not model.

## Reproduce and verify

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/single_caller_study.py \
  --out /tmp/nokia-single-caller-study
```

[Summary](results/single-caller-study/summary.json),
[swapped-role witness](results/single-caller-study/example-preparation-source-07-swap-1-mask-0.json),
and [original-role witness](results/single-caller-study/example-preparation-source-31-swap-0-mask-7.json)
retain the assumptions and complete example traces. All nine artifacts
regenerate byte for byte. The functional/assumption suite passes 52 tests,
including a comparison of the local harness to the integrated runner at the
55-instruction zero-input path and tests of both surviving marked-input
representations. The full plan remains incomplete.
