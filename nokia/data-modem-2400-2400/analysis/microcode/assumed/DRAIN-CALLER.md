# The caller combines three input-dependent shift loops

The only direct caller of 296 is BSR 249 inside wrapper 248–24E. The wrapper
itself is called at 150 and 157. Under the fitted-original mapping it does
not initialize R7, so the mask dependence found in [BIASED-DRAIN.md](BIASED-DRAIN.md)
is a caller precondition rather than something resolved inside the wrapper.

The wrapper executes this sequence:

1. 248 writes `2*(D+Q) mod 256` to R3.
2. 249 calls 296, including its two setup writes and right-shift loop.
3. 24A replaces R3 with R2.
4. 24B calls 298 directly, running the right-shift loop a second time with
   the Q left by the first call.
5. 24C leaves Q unchanged. 24D calls the left-shift loop at 187.
6. 24E returns, with a transient ALU output of R7+R4 under this decode.

These are sequential calls. Passing the first right-shift loop does not
establish that the second loop or the left-shift loop will return.

## Left-shift loop

187 computes F=`(D+Q) mod 256`, writes `2*F mod 256` to R0, and shifts Q
left once with zero fill. BLT at 188 tests the **previous** zero flag from
187. It therefore returns exactly when the pre-shift Q is `-D mod 256`.
If continued shifts reach Q=0 while D is nonzero, the complete state repeats
in the two-instruction cycle `187 → 188 → 187`.

After that loop exits, 189 clears Q and 18A writes `(D+1) mod 256` to R0.
This explains the final state of returning wrappers; it is not an established
multiply, divide, or physical timing function.

## Exhaustive local caller experiment

The [study](drain_caller_study.py) starts at the actual BSR 150, so both the
wrapper return and its nested calls use the unmodified circular-stack model.
It tests all 256 initial Q values against all 256 constant external D values
for each R7 mask, keeping R2=35, R13=A5, zero shift fill, and the existing
original-register/previous-flag policy.

| R7 | Wrapper returns | Repeats in first right loop | Repeats in second right loop | Repeats in left loop |
| --- | ---: | ---: | ---: | ---: |
| 00 | 2,124 | 0 | 0 | 63,412 |
| FF | 256 | 63,359 | 1,665 | 256 |

For R7=FF the full wrapper returns only for D=00, for every initial Q. D=80
passes both right loops but then repeats in the left loop. These are
consequences of holding D constant throughout the call, not proof that actual
hardware holds that input constant or reaches the supplied register states.

Every case matches the composed analytic termination prediction. On return,
Q=0, R0=`(D+1) mod 256`, and R3=R2; other registers are preserved. Non-return is
established by repetition of complete local machine state at a loop header,
not by reaching a timeout. Six representative stage/mask combinations also
replay through the ordinary integrated executor with matching final PC/RAM/Q.

The [report](results/drain-caller-study/report.json) stores outcome counts,
returning input sets, repetition periods, full witnesses, and source/execution
hashes. [Configuration](drain-caller-study.json) declares the assumptions.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/drain_caller_study.py
```

The study additionally records 512 reset-driven, 1,000-cycle runs with zero
initial RAM/Q: 256 hold D constant everywhere; 256 use the earlier successor-byte
profile (18D reads X, 1EC reads X+1, other instructions read zero). Those bounded
runs distinguish local caller experiments from paths reached under the selected
reset scenarios; they do not establish every possible caller state or external
input sequence. None of the 512 runs visits 150, 157, or the wrapper. All
constant-input runs remain at 1EC/1ED; all successor-response runs reach the
terminal loop at 084. Thus the local repetition cases are not a contradiction
of these tested reset paths. The path that enters either caller with meaningful
inputs remains unresolved.

The default mapping and scenario are unchanged. This result strengthens the
need to recover caller register values and external-D behavior, or revise the
condition/datapath hypothesis if further evidence contradicts it. It does not
justify forcing loop exits or labeling arbitrary local inputs as real hangs.
