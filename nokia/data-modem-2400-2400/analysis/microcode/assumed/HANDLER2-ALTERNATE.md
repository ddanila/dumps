# Handler 2: alternate carry preparation and computed return leaves

*Runs under the [shared assumptions](ASSUMPTIONS.md).*

The 1E0–1E4 alternative selects the later comparison byte using an input sum's
carry and the handler code. It replaces the normal 196–19B preparation and
rejoins 19C. Four one-word return leaves at 1E5–1E8 produce different temporary
R3 values before the common body overwrites them. Their addresses are selected
from an actual preceding ALU result in the experiments below.

## Entry is a separate condition-source hypothesis

Under the existing q3 previous-zero source for selector 7, this reset path
**does not enter 1E0**. 194 preserves R0=c, where handler-2 codes are
c=2,10,...,250. Its zero flag is always false, so 195 falls through to 196.
Changing later input bytes does not release that condition.

This study explicitly changes selector 7 to a direct external line, initially
low and rising at cycle 92, when 195 executes. Other condition sources retain
their established meanings. All PC, ALU, RAM/Q and stack transitions before
cycle 92 match the original reset trace for each code. Two negative controls
per code retain the original zero source or delay the rise to cycle 93; both
continue to 196. The positive cases are evidence for this declared alternative,
not proof that the Nokia condition multiplexer has this connection.

Use the existing PLP replies, zero reset and later table index 2, except for
the explicit 1A2 index source described below. Let e=D1E1, b=D1A2 and p=D1D0
be independently supplied bytes. Let k count unsuccessful poll replies.

## Carry-selected comparison byte

At 195, R0=Q=c and R3=1. R15 is zero. The OR at 195 produces carry one for
these codes, and 1E0 exposes Q with that carry. The next instructions are:

| Address | Effect |
| --- | --- |
| 1E1 | Temporarily store R4=(c+e)&FF; carry h is one iff c+e>=256 |
| 1E2 | Store R0=0; test the previous carry h and skip 1E3 iff h=1 |
| 1E3 | On h=0, restore R0=c |
| 1E4 | Expose R0+Q+1, then branch unconditionally to 19C |
| 19C | Replace R4 with FE plus the carry from 1E4 |

If h=1, 1E4 computes c+1, which cannot overflow for these codes. If h=0,
it computes 2*c+1, carrying exactly when c>=128. Therefore the retained
comparison value is:

```
h = (c+e >= 256)
r = 254 + int(c >= 128 and not h)
```

Q remains c throughout. D197 is bypassed, so the normal path's comparison
formula based on that input does not apply. The value read at 1E2 is also
irrelevant to retained state: its ALU expression is NOT(D) AND zero. The skip
uses 1E1's carry, not the flag calculated by the current instruction.

## Four data-indexed return leaves

At 1A1, Q=c and the preceding carry from 1A0 is zero. Supply
D1A1=(c+1+j)&FF for j=0,1,2,3. Its subtraction exposes Y=j. The declared
`previous_y` index source at 1A2 consequently selects target 1E5+j. This
changes only that site's index source; the initial transform, later paired
wrapper and terminal stores retain index 2.

1A2 itself computes Q=s=(c+b)&FF. Let t be the carry from that sum. With
R3=1 on entry, the four POP operations leave:

| Index j | Target | Temporary R3 |
| --- | --- | --- |
| 0 | 1E5 | 254+t |
| 1 | 1E6 | 1+t |
| 2 | 1E7 | t |
| 3 | 1E8 | t |

Each consumes the real BSR frame and returns to 1A3. These are transient
arithmetic alternatives, not four distinct retained outputs: the subsequent
body overwrites R3. All four preserve Q=s and take one instruction. Reset
checks verify the leaf's ALU value, return address and stack depth separately
from final-state equality.

## Common body, reply and complete result

The continuation uses the [existing handler-2 body](HANDLER2-BODY.md): drain
s, clear the intermediate state, take the default 2D0 detour, capture R4 into
R12, load payload p, and poll for a reply at 1EC. A successful reply is
(-r)&FF. Supplying one larger byte for k visits makes each fail with sum one;
the final matching reply returns with R3=0.

Final Q=p, R0=R2=p>>1, R5=((-p)&FF)>>1 and R12=r; every other register is
zero. This is independent of leaf index j. The payload arithmetic wraps to
eight bits before shifting. First-poll and terminal cycles are:

```
first poll     = 180 + 2*bit_length((c+b)&255) - h
first terminal = 212 + 2*bit_length((c+b)&255) - h + 2*k
```

The alternate preparation is one instruction shorter than the normal body,
with another instruction saved when 1E2 skips 1E3. All runs reach terminal
with zero active stack depth; maximum depth is three. These are modeled
microinstruction counts, not hardware completion or sample timing.

## Verification and scope

The actual arithmetic is checked locally for all 8,192 code/e combinations
and 32,768 code/b/leaf combinations. Complete reset checks cover 1,536 cases:
all 32 codes, e immediately below/at the carry threshold and at 00/FF, three
b/payload pairs, and all four leaves. Diagnostic reply delay varies from zero
to two. There are 64 negative entry controls and eight saved full witnesses
covering both carry outcomes and all leaves at code 82.

Checks compare the full final RAM/Q, input provenance, previous-Y index,
intermediate carry and leaf result, poll values, timing, prefix equality and
stack behavior. Regression tests add independent random inputs and delays,
change bypassed/transient inputs, compare different leaf indices, and repeat
negative entry controls. Witnesses replay without injected RAM or stack.

The original selector-7 zero policy remains valid for its existing scoped
studies and still excludes this branch. The external-line alternative and
site-specific index source remain hypotheses. No physical input protocol,
transient Y consumer or modem algorithm is inferred from their successful runs.

[Configuration](handler2-alternate.json), [runner](handler2_alternate.py),
[report and witnesses](results/handler2-alternate/report.json).

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/handler2_alternate.py
```
