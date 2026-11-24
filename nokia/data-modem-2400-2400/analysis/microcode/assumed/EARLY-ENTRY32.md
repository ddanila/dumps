# Early entry 032: nested choices and comparison-input selection

*Runs under the [shared assumptions](ASSUMPTIONS.md).*

Entry 032 has four declared continuations at 036. Two of them reach another
three-entry branch at 03C. The paths select which input difference survives in
R3, and therefore whether the shared Q/R3 wait returns. Two additional branch
conditions change timing without changing the final state formula.

This is q3 with previous flags and zero reset. The early selector remains
false. D002=5 and D076=1 establish preceding Y=6 at 008; an explicit
preceding-Y hypothesis selects early entry six, 032, while 008 itself replaces
Q with FF. The first later index i=0..3 is a scenario parameter at 036. The
second index j=0..2 comes from D03B through a separate preceding-Y hypothesis
at 03C. These are declared index sources, not recovered physical wiring.

## Preparation and surviving comparison value

032 computes Q=1 from reset R0=FF and R15=0. Let a=D033, b=D034, w=D03C,
z=D036, c=D05B and t=D064. 033 writes a shifted difference to R3 and produces
carry one exactly when a is nonzero. 034 overwrites R3 with
(b-2+int(a!=0))&255. 035 exposes another input-dependent difference. 036 writes
R4=(z+1)&255 while selecting its continuation; this R4 is later overwritten.

The dispatch paths are:

| i | First path | Reaches 03C? |
| --- | --- | --- |
| 0 | 037 → 047 → 048 → 045 | no |
| 1 | 038 → 049 → 04A → 04B → 03B | yes |
| 2 | 039 → 040 → 041 → 042 → 045 | no |
| 3 | 03A → 03B | yes |

03B exposes j. At 03C the arithmetic writes R3=(w-1)&255 independently of
its branch index, then dispatches to 03D, 03E or 03F:

- j=0: 03D branches to 040.
- j=1: 03E branches to 047.
- j=2: 03F performs a conditional skip before the 040/041 sequence.

Thus the comparison value r reaching the shared wait is:

```
i=0 or 2: r=(b-2+int(a!=0))&255
i=1 or 3: r=(w-1)&255
```

The second dispatch replaces the earlier difference; the discarded 033 shift
and temporary R2/R0 captures do not determine the final comparison value.

## Two timing distinctions

03F tests the previous zero flag from 03C's w-1 result. It executes 040 only
when w=1; otherwise it skips directly to 041, saving one instruction. Its own
arithmetic also writes R0, but the later shared wait overwrites that value.

On i=1, carry from z+1 at 036 propagates through 038 and 049 into 04A. It leaves
R0=1 for z=FF, otherwise R0=0. If j=1 subsequently takes 047/048, the value
exposed at 048 makes 045 branch directly to 05B when z=FF. Otherwise 045 falls
through to 046, which branches back to 00B; 00B/00C then reach 05B. That longer
path costs three extra instructions.

For i=0 and i=3,j=1, R0 is still FF at 047/048 and 045 takes 05B directly.
For paths through 041, R1=R15=0 makes its sum noncarrying. 042 therefore branches
to 045, bypassing 043 and the 044 call. Those two words are deliberately not
included in these new annotations.

## Complete timing and state

The first 05D cycle is:

| i | j=0 | j=1 | j=2 |
| --- | ---: | ---: | ---: |
| 0 | 29 | 29 | 29 |
| 1 | 36 | 35 if z=FF, otherwise 38 | 36 if w=1, otherwise 35 |
| 2 | 30 | 30 | 30 |
| 3 | 33 | 32 | 33 if w=1, otherwise 32 |

The j value is not read in rows i=0/2. All paths arrive with Q=1 and R3=r.
If r is not one, the exact seven-instruction recurrence at 05D has stable state
Q=1, R0=2, R2=R3=r, R4=(c+1)&255, and all other RAM registers zero.

If r=1, the wait returns on its first pass. The first 084 cycle is the table
entry plus 18. Its complete terminal state is Q=1, R0=R2=2, R3=(t-2)&255,
R4=(c+1)&255, with all other RAM registers zero. Maximum stack depth is one,
and terminal runs finish with depth zero. No terminal arrival is equated with
a physical completion signal, and transient Y values have no assigned consumer.

## Evidence

The study executes 768 complete 192-instruction reset cases covering all twelve
i/j combinations, zero/nonzero a, boundary b/w values, and both ordinary and
FF z. Each run checks every final RAM/Q value, both dispatches, the conditional
skip, the path through 046, wait-entry timing, terminal timing or exact state
recurrence, and stack depth. Independent randomized regressions vary all data
bytes, and explicit cases verify successful return for every index pair.

Twenty-six saved witnesses cover the branch and timing variants. Every newly
annotated address is reached by a saved reset trace; 043/044 are excluded.
The supplied indices and external bytes remain hypotheses. This is not an
exhaustive arbitrary-state interpretation of the early control region.

[Configuration](early-entry32.json), [runner](early_entry32.py), and
[report](results/early-entry32/report.json).

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/early_entry32.py
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -p 'test_*.py'
```
