# Retained q2 mapping interprets the mask loop as an external poll

Comparing the existing six mappings gives a concrete alternative to the
[fitted-original mask-loop interpretation](MASK-LOOP.md). With mapping **q2**
and an explicitly shared previous-flag/defined-logical-carry policy, 12C–130
waits until external D equals a masked Q value. No instruction-specific exit
rule or new field assignment is introduced.

q2 is the previously retained Q-independent mapping with source controls
I0=17.5, I1=18.2, I2=18.6. Its paired-arithmetic constraints and limitations
are documented in [Q-INDEPENDENT.md](Q-INDEPENDENT.md). The flag policy used
here is a separate declared hypothesis, not an assertion that earlier q2
experiments established that global condition wiring.

## How the alternatives differ

Let M=R0, Q0 be Q on loop entry, and T=Q0 AND M. Under the shared previous-flag
policy, the loop predicates and Q updates are:

| Mapping | Condition for return | Q after masking |
| --- | --- | --- |
| q1 | M=0 | 0 |
| q2 | External D at 12E equals T | T |
| q3 | M=0 | 0 |
| q4 | M=0 | T |
| fitted_original | T=M | T |
| fitted_swapped | T=R7 | T |

The distinction comes from the decoded ALU source fields. At 12E, q2 selects
D and Q, computing `Q−D mod 256`; fitted_original selects R0 and Q. q1/q3/q4
instead compute R0 with the chosen carry policy. Swapping the register fields
makes the fitted alternative compare against R7.

For q2, 12C stores `(D_at_12C + Q_before_mask) mod 256` in R2; 12D masks Q;
12E performs the external comparison; and 12F uses that previous zero flag
for its BLT decision. A repeated pass leaves masked Q fixed, but a later D
sample at 12E can satisfy the comparison. D need not have the same value at
12C and 12E. A returning 130 leaves masked Q unchanged.

## Verification

[mask_variant_study.py](mask_variant_study.py) compares 16 common register/Q
fixtures against every constant D byte for each mapping: 24,576 comparisons.
It checks each mapping's independently stated return predicate and full final
RAM/Q, including source/destination differences in the copy at 12C.

For q2 it then exhausts all 65,536 mask/Q pairs with:

- D=T: return on the first pass, with the predicted R2 and masked Q.
- D=T XOR 1: an exact four-instruction repeated state.
- A changing operand only at 12E: first T XOR 1, then T held thereafter.
  All 65,536 calls return on the second pass. Other addresses read 5A.

This totals **221,184 comparisons**. Thirteen representative witnesses also
run through the ordinary integrated executor, matching final PC, all register
RAM and Q. Changing-input witnesses log the actual external-read sequence;
they do not inject flags, PCs, stack entries or register results.

The [report](results/mask-variant-study/report.json) records decoded sources,
case counts, full witnesses, source hashes and an execution digest. The q2
constant-input counts include both the common fixtures and its additional
exhaustive checks, so raw counts across mappings are not a quality ranking.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/mask_variant_study.py
```

[Configuration](mask-variant-study.json) declares the common condition policy,
fixtures and diagnostic input. The mappings themselves remain unchanged.

## What this establishes

This meets the immediate need to feed routine interpretation back into the
retained datapath alternatives: q2 supplies a coherent changing-input meaning
where fitted_original supplies an idempotent internal test. Its superiority
is local to that interpretation, not a proof that this routine should poll
external data or that q2 is globally correct.

The physical input channel, caller-selected target, surrounding reset behavior
under q2, and compatible condition sources elsewhere still need validation.
The q2 mapping is not promoted to the default. The fitted-original reset
counterexamples remain valid under their own explicitly recorded assumptions.
