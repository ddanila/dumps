# Three q3 conditional helpers

Actual local calls to 270, 335 and 357 distinguish conditional register
updates from branches that change only transient output. These are q3
interpretations with previous ALU flags, the declared ripple logical-carry
model, and independently selectable **constant** tests for selectors 5 and 6.
They do not establish physical condition wiring or reset reachability.

Every run begins at a real BSR with arbitrary declared RAM/Q and an empty
stack. It returns through the real POP to the caller's next instruction.
No return address or intermediate machine state is injected.

## 270–27F: input capture and overflow-selected copy

Use `a=old R0`, `b=old R3`, and `v=D271`. The retained result is:

- Q=v and R2=old R1.
- R0=v if a+b >= 256; otherwise R0=a.
- All other RAM is preserved.

272 tests the carry from 271, which adds the byte input to zero with carry-in
zero. Its carry is always zero, so the inverted-carry test skips 273.
Similarly, 277 copies R1 by adding it to zero with carry-in zero. Its carry
is zero, so 278 always branches over 279–27A. These three bypassed words are
explained by the preceding arithmetic, not merely absent from sampled traces.
Different flag timing or condition wiring can invalidate that exclusion.

27C adds old R0 and R3 without saving the result. The inverted-carry test at
27D skips 27E when the sum fits in a byte, and otherwise executes 27E to copy
Q into R0. The final POP exposes R1+R3 modulo 256. Earlier transient values
include D270+old Q, NOT(D275) AND v, D276+v, and D27B+v; none is assigned a
physical output consumer.

The helper executes 12 instructions without overflow and 13 with overflow;
the BSR adds one. All 65,536 R0/R3 pairs split into 32,896 non-overflows and
32,640 overflows. R2's earlier R0 copy at 274 is overwritten at 277.

## 335–340: optional captures and Q complement

Let `q=old Q`, `s5` and `s6` be the declared constant condition tests, and
`Dxxx` the external byte read at that address.

- R4=D336 in every path.
- If s5=0, R12=(D338+q)&255 and R0=D339 AND q. If s5=1, both are preserved.
- If s6=0, Q=q XOR FF; if s6=1, Q=q.
- All other RAM is preserved.

337 bypasses the two optional writes when s5=1. At 33C, s6=1 branches to the
alternative POP at 340, which exposes zero. With s6=0, execution falls through
33D, whose identical constant test also stays false; 33E complements Q and
33F exposes the updated R0. A test that changes between 33C and 33D is outside
this constant-selector contract.

| s5 | s6 | Helper instructions | Return | Final Y |
| --- | --- | --- | --- | --- |
| 0 | 0 | 11 | 33F | Updated R0 |
| 0 | 1 | 9 | 340 | 0 |
| 1 | 0 | 9 | 33F | Preserved R0 |
| 1 | 1 | 7 | 340 | 0 |

The complement is one's complement (`~q & 255`), not arithmetic negation.
The input at 336 does not become the source of 339 under q3: 339 reads a new
external D byte and masks Q with it. This is a useful source-field constraint
for any proposed interpretation of the routine.

## 357–360: shared state, three different return sums

All paths preserve Q, set R0=old R1 and R4=(D359+Q)&255, and preserve all other
RAM. The early transient sequence includes old R15, followed by the carry
chain:

```
t = D359 + Q
u = D35A + Q + (t >= 256)
y35B = (D35B + (u >= 256)) & 255
```

Only the low byte of t is retained, in R4. 35C exposes old R1 OR Q.

| Condition | Return | Final Y, modulo 256 | Helper instructions |
| --- | --- | --- | --- |
| s5=1 | 360 | R12+R2 | 7 |
| s5=0 and (old R1 OR Q) != FF | 35E | R12+R3 | 8 |
| s5=0 and (old R1 OR Q) == FF | 35F | R12+R1 | 8 |

The last two cases follow from the selected OR carry equation: with carry-in
zero, OR produces carry one exactly when its result is not FF. 35D tests its
inverse using the previous flag. The 65,536 R1/Q pairs produce 6,561 returns
through 35F and 58,975 through 35E when s5=0. Thus the return choice can change
the ALU bus while leaving final RAM/Q identical. There is no identified
external strobe or consumer for those sums.

## Evidence and scope

The study checks 458,752 actual local calls: one 65,536-case plane for 270,
four for 335 (each constant s5/s6 pair), and two for 357 (each s5 value).
Every case checks complete final RAM/Q, instruction count, every helper PC and
every transient Y against independently written formulas.

The swept planes are explicit rather than exhaustive over all machine state:

| Entry | Two independent swept bytes | Other varied fixture data |
| --- | --- | --- |
| 270 | R0=a, R3=b | old Q=a XOR A5; D271=a XOR b; remaining reads have stated a/b formulas |
| 335 | D338=a, Q=b | old R0=a XOR 37; D336=b XOR 7F; D339=a XOR 55 |
| 357 | old R1=a, Q=b | D359=a XOR 55; D35A=a XOR 7F; D35B=a XOR FF |

All constants in this table are hexadecimal. The runner declares every other
register and external read. Its 28 saved boundary witnesses compare every
recorded step, including ALU flags, carry input, register changes and stack
slots, against the ordinary executor. A regression test additionally compares
192 calls with independently randomized registers and per-PC input bytes
against that executor, covering all nine distinct helper paths. Those cases
break the correlations in the exhaustive planes.

No new reset coverage is claimed. The 270 caller at 120 lies after the
handler-0 mask wait discussed in [SHORT-HELPERS.md](SHORT-HELPERS.md); a local
contract is useful even when that particular reset scenario cannot reach it.
Physical input meanings and the consumers of transient sums remain open.

[Configuration](branch-helpers-study.json), [runner](branch_helpers_study.py),
and [report and witnesses](results/branch-helpers-study/report.json).

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/branch_helpers_study.py
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -p 'test_*.py'
```
