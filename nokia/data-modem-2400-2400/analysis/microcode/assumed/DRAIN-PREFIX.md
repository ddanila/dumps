# The caller overwrites the first drain result before consuming it

*Runs under the [shared assumptions](ASSUMPTIONS.md).*

The [30B mapping comparison](MASKED-DRAIN.md) found different retained R5
values under q2 and fitted_original. The actual local caller prefix at
304–308 invokes that helper twice. Its second call overwrites R5 with zero,
and no selected operand or ALU-Y path consumes the first R5 value in between.
The difference remains visible in transient state and duration, but does not
survive as R5 at the next wrapper call.

## The complete prefix

The [study](drain_prefix_study.py) executes these real calls and stops at 309,
before the paired-arithmetic wrapper at 370:

1. 304 calls 30B, which clears R0/Q and produces the mapping-dependent R5.
2. 305 calls 311. Since Q is now zero, 311 stores its external byte in R12.
   Instructions 312–313 expose further ALU results without changing RAM/Q.
3. 306 calls 30B again. Its R0/Q inputs are both zero, so both mappings take
   one iteration and write R5=0.
4. 307 calls 311 again, replacing R12 with this visit's external byte.
5. 308 calls 314, whose successive writes leave different final preparation
   registers under the two mappings.

Let d1 and d2 be the bytes supplied to the two 311 visits, and e0–e3 those
supplied at 314–317. With r10/r11 denoting the original register values:

| State on reaching 309 | q2 | fitted_original |
| --- | --- | --- |
| R0, R5, Q | All zero | All zero |
| R12 | d2 | d2 |
| R13 | r11 | e2 |
| R4 | r10 | e3 |
| Other RAM | Preserved | Preserved |

Under q2, 314 and 316 copy R3 then R11 to R13; 315 and 317 copy R2 then R10
to R4. Under fitted_original those instructions write D+Q, with Q=0, to the
same destinations. The first two preparation results are therefore overwritten
by the last two in both interpretations. The first 311 byte is likewise
replaced by the second. These statements concern internal state; they do not
rule out unidentified physical consumers of transient ALU values.

q2 takes 28 instructions from 304 through the return to 309. fitted_original
takes 28, 30, 32, 34 or 36 according to the first drain's iteration count.
Thus the first helper still affects duration even though its retained R5 is
later erased. The caller cannot be used to select a mapping merely by looking
at final R5 or whether both calls return.

## A scenario gate prevents claiming reset reachability

Instruction 302 is a select-5 branch to 319. In the existing shared scenario,
select 5 is a constant zero source with inverted polarity, so this branch is
always taken. Execution entering at 300 therefore bypasses 303–308. The new
study explicitly starts at 304; it neither silently changes that condition
nor claims a reset path into these calls. Recovering or varying this condition
is a separate hypothesis to test. The caller's later 370 loop is also outside
this prefix's completion claim.

## Verification

The reference predicts the complete final RAM/Q array, first retained R5 and
cycle count for **139,264 local cases**: all 65,536 R0/Q combinations for each
mapping, plus 4,096 seeded fixtures per mapping with independently varied
initial RAM, Q and the six external bytes. Reads at the two 311 visits are
supplied separately, so preservation of d2 is not inferred from equal inputs.

The component probe also rejects any instruction in the executed prefix that
selects R5 as an ALU operand or forwards it via Y=A. Twenty-three integrated
witnesses match the component probe instruction by instruction, including Q,
ALU results, flags and branch decisions. Actual calls and returns use the
sequencer stack. No register or branch result is injected.

This adds caller context to the prior local discriminator: its R5 difference
is transient here, while other preparation registers and duration still
distinguish the mappings. It does not identify a modem algorithm, physical
input channel or output consumer. Defaults remain unchanged.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/drain_prefix_study.py
```

[Configuration](drain-prefix-study.json) and
[report](results/drain-prefix-study/report.json) retain the fixtures, complete
witnesses, comparison digest and source/trace hashes.
