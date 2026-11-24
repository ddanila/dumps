# The q3 input-preparation and comparison tail at 2EC

2EC–2FC prepares input-dependent registers, chooses one of three paths into a
shared tail, and returns through two real nested calls. With the declared
21F dispatch entry, the paths produce different transient Q/Y values and take
different times but leave the same final RAM/Q for the same initial state and
external inputs.

This is a local q3 contract using previous flags, a constant selector 1 and
the default unconditional direct-BRT policy. The initial PC is the actual
caller at 212, with an empty stack. Dispatch at 21F uses existing scenario
index 2 in the ROM-derived table, which targets 224. Other table choices and
optional BRT gates are not silently included in the contract.

## Final state

Write `a=old R0`, `q=old Q`, `Dxxx` for the byte read at that address, and
`z=(q+D2EF)&255`. The complete returned state is:

| Register | Returned value |
| --- | --- |
| R2 | old R1 |
| R3 | `(a + (D2F1+z >= 256)) & 255` |
| R4 | `(D2EC+1) & 255` |
| R5 | `(old R5-a-1) & 255` |
| R15 | `D2F0 XOR z` |
| Q | D225 |
| All other RAM | Preserved |

2EC first captures D2EC in R4; the shared tail increments it at 21A. 2EE
writes the complement of old R3, but 2F2 overwrites it with a plus the carry
from the preceding input sum. 2F0 captures an XOR using a new external D byte;
it does not use R4 as its source under q3. These overwrites and source choices
matter when interpreting the routine as input processing.

The final Q is neither z nor one of the intermediate masks. The nested leaf
at 225 replaces it with its own input byte. This is why changing the local
route does not change final Q under this fixed dispatch hypothesis.

## Three routes

2F4 adds a to zero with carry-in zero, so its carry is always zero. Therefore
the previous-carry test at 2F5 cannot branch. Its arithmetic computes
`a-old R7-1`; the carry is one exactly when a>old R7. 2F6 tests that carry.

| Route | Condition | Q on entry to 3BB | Total instructions including caller |
| --- | --- | --- | ---: |
| Comparison | a>old R7 | `D2F3 AND z` | 28 |
| Selector | a<=old R7 and selector 1 true | D2F7 | 32 |
| Reload/mask | a<=old R7 and selector 1 false | `D2E0 AND D2E1` | 39 |

The comparison route branches at 2F6. Otherwise 2F7 loads Q from an external
byte. A true constant selector 1 branches at 2FA; a false one falls through
2FA and 2FB, then 2FC jumps to 2E0. That continuation loads a new byte and
masks it with another, before 2E4 transfers to 3BB. Because the same constant
selector is false at 2E3, that TSK does not bypass 2E4.

Thus 2F5 and 2FB do not take their branches under these policies, for distinct
reasons: the former follows a provably zero arithmetic carry; the latter is
reached only when the shared constant selector is false. A changing external
selector or different flag timing could invalidate this path exclusion.

## Shared tail and real return

3BB writes `old R5-a-1` into R5; 3BC transfers to 2FD under the default BRT
policy. 2FD exposes a difference using the prepared R3 and intermediate Q.
2FE calls 21A, whose code increments R4, copies R1 into R2, exposes Q and makes
the computed call at 21F.

The declared table index selects 224–227. This leaf exposes `R15-a`, loads Q
from D225, exposes zero and then Q, and pops to 220. 220 pops to 2FF, which
pops to 213, the real caller's continuation. Maximum stack depth is three and
final depth is zero. No return frame is injected, suppressed or repaired.

These local runs validate the tail's calling convention with a live incoming
frame. They complement [TAIL-STACK-CONTRACT.md](TAIL-STACK-CONTRACT.md), whose
broader graph analysis explains why entering the same tail without a frame
can underflow. This study does not claim all graph entries are safe.

## Validation

The study checks 262,144 calls across two complete byte planes, each with both
constant-selector settings:

| Plane | Independent bytes | Other fixture choices |
| --- | --- | --- |
| Comparison | R0=a and R7=b | Q=77 decimal; D2EF=b XOR A5 |
| Input sum | old Q=a and D2EF=b | R0=128 decimal; R7=127+(a AND 1) |

Other external bytes have explicit a/b formulas in the runner, and other RAM
starts nonzero. Hexadecimal constants use their usual A–F notation. These
planes are not an exhaustive sweep of all initial state. Every call checks all
final RAM/Q, every helper PC/Y value and instruction count against independently
written formulas.

For each comparison-plane selector, 32,640 cases use the comparison route and
32,896 take its complementary route. For each input-sum-plane selector, the
split is 32,768/32,768. Twenty saved boundary witnesses compare every local
step against the ordinary executor, including flags, carry input, register
changes and stack slots. Ninety-six independently randomized register/input
calls cover all three routes and additionally flip selector 1 to check equal
final RAM/Q despite potentially different traces and durations.

No new reset reachability is claimed. Physical input channels and the consumer
of transient Y remain unresolved. The fixed dispatch entry is essential to
the final-Q formula; it is a hypothesis, not a discovered controller command.

[Configuration](input-tail-study.json), [runner](input_tail_study.py), and
[report and witnesses](results/input-tail-study/report.json).

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/input_tail_study.py
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -p 'test_*.py'
```
