# Following preparation bytes through the caller chain

*Runs under the [shared assumptions](ASSUMPTIONS.md).*

The A/B swap can make 341–344 write R10–R13, but that alone does not explain
useful operand flow. In the tested 133 caller path, later table calls remove
the preparation-byte effects from the final internal state. With the original
register roles, some effects survive in R0–R3 while the transform source
pairs remain zero.

This experiment follows the real caller and callee instructions without
checking for an expected rotation formula. It is still restricted to the
sixteen source layouts retained by the previous arithmetic search and their
A/B swaps; it is not an unconstrained search for a different algorithm.

A [follow-up on the alternate 18B caller](SINGLE-CALLER.md) finds surviving
input effects under both register-role hypotheses. The loss reported here
does not generalize to all caller paths.

## Explicit local fixture

[chain-search.json](chain-search.json) starts at 133 with an empty stack,
zero RAM, and Q=00 or 55. Execution follows the actual call to 341, returns
through the instructions at 134–13A, then calls 3EA, 3D5 and 3C0 in order.
It stops before 13E. Branches 139 and 13A fall through. Each table wrapper
runs once: BLT at 3ED, 3D8 and 3C3 exits. All other conditional tests default
false; the scenario's unconditional transfers are retained.

The three computed calls independently choose one of their four entries,
giving all 64 combinations. These choices are fixture inputs, not recovered
datapath-driven dispatch. D is zero except at 341–344, where the four supplied
bytes are sampled in instruction order. Carry uses the existing mapped/previous
policy with its explicit unknown-carry fallback.

For each of 32 profiles, 64 entry combinations and two initial Q values, the
study runs an all-zero D baseline plus eight perturbations: each of the four
bytes independently set to 01 or 80. That gives 36,864 primary fixture runs.
Another 64 runs save complete traces of zero versus marked bytes 12,34,56,78
for the all-entry-zero example. Every run takes 42 instructions, reaches the
stop with balanced stack, and has maximum stack depth three. These local
entries contribute nothing to reset coverage.

## Observed sensitivity

The four D,Q source candidates (07,23,27,31) have the same result. The other
twelve candidates do not select D in the preparation routine, so changing
only those four D bytes does not affect their internal states.

For the D,Q candidates with original register roles:

- After preparation, the first two input bytes leave no observed checkpoint
  effect. The third can affect the fourth computation through carry; the
  fourth directly affects R0.
- After all three calls, the observed register differences are confined to
  R0–R3. Neither Q nor checkpoint Y changes in these perturbation comparisons.
- Per input byte there are 256 comparisons: 64 entry combinations × two Q
  values × two perturbations. The third byte changes R0–R3 in 192 comparisons;
  the fourth does so in all 256. R10–R13 remain zero in the saved examples.

With swapped register roles, the preparation bytes initially affect R10–R13.
Some effects survive the first and second calls, depending on table entries.
After the third call, **none of the tested single-byte perturbations changes
any RAM register, Q, or checkpoint Y**, across all 64 entry combinations and
both Q values. This is finite sensitivity evidence, not a proof of independence
for every possible byte combination or initial state.

The marked example for candidate 07, swapped roles, Q=00 and entries (0,0,0)
shows the loss directly. Values below are hexadecimal:

| Checkpoint | R10 R11 R12 R13, marked inputs | Same registers, zero inputs |
| --- | --- | --- |
| 134: after preparation | EE CB AA 87 | 00 00 00 00 |
| 13C: after first table wrapper | AA 87 00 00 | 00 00 00 00 |
| 13D: after second wrapper | 00 00 00 00 | 00 00 00 00 |
| 13E: after third wrapper | 00 00 00 00 | 00 00 00 00 |

In that example the complete final RAM, Q and checkpoint Y match the zero-input
run, not just these four registers. The full traces preserve intermediate ALU
outputs; no physical write enable or external recipient is assigned to them.

## What this changes

A plausible preparation destination is insufficient evidence for a global
register-role swap. The surrounding instructions and subsequent calls must
also preserve or deliberately consume the data. Conversely, loss from final
internal state does not establish that the hardware discards it: external
transfers between checkpoints are still unmodeled.

This experiment covers the 133 three-call path only. The separate 18B caller
calls 341 and then 3EA without immediately following it with both other
wrappers; its later use of the result needs separate analysis. Repeated loop
iterations, other condition choices, nonzero initial RAM, different source
layouts and external memory operations remain open. No candidate is promoted
or rejected as physical wiring solely from this local experiment.

## Reproduce and verify

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/chain_study.py \
  --out /tmp/nokia-chain-study
```

[Summary](results/chain-study/summary.json),
[original-role example](results/chain-study/preparation-source-07.json), and
[swapped-role example](results/chain-study/preparation-source-07-swap.json)
contain checkpoint sensitivity counts and complete marked/zero example traces.
The functional/assumption suite passes 51 tests. The new test matches the
local harness to the main integrated runner for a zero-input example, including
its final PC, RAM and Q, then verifies preparation loading and subsequent loss
in the swapped example. All 33 artifacts regenerate byte for byte. The full
plan remains incomplete.
