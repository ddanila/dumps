# Handler 3: alternate drains and a transient paired component

*Runs under the [shared assumptions](ASSUMPTIONS.md).*

A new, explicitly declared condition-source hypothesis reaches 1EF–1FF from
zero reset. It explains the previously bypassed body as temporary component
construction, two Q drains and register preparation before rejoining 308.
The component survives into the paired arithmetic outputs even though the
terminal tail later overwrites its register.

## Entry premise and controls

The mapping is q3 with previous flags and matched PLP-side early replies.
Input code c=3,11,...,251 selects handler 300. A common external line starts
high and falls at microcycle 43. Selector 5 uses this line directly; selector
3 uses its inverse. Thus 302 at cycle 43 falls through, and 303 at cycle 44
branches to 1EF. No runtime PC, branch target or stack frame is patched.

This changes a condition-source assumption: selector 3 normally tests inverted
carry. It does not establish that the board shares an external line between
these mux inputs. Both assignments and the scheduled transition are labelled
in [the configuration](handler3-drains.json).

Two controls for every code demonstrate the entry boundary:

- Keep selector 3 on inverted carry: the same falling selector-5 line reaches
  the existing 304 continuation, without entering 1EF.
- Fall at cycle 44 with both new assignments: 302 has already selected 319,
  so execution again excludes 1EF.

For all successful experiments, cycles 0–42 have identical PCs, next PCs,
ALU results, RAM writes, Q and stack states to the existing baseline for that
code. Extra condition-read metadata is not treated as a state difference.
This preserves the existing early execution evidence while keeping the new
entry premise explicit.

## Temporary construction and two drains

Entry occurs at cycle 45 with R0=FF. 1EF copies R0 into Q. At 1F0, input f
is added to FF, and the byte result is shifted left into R5. Q independently
shifts from FF to FE. 1F2 reloads FF from R0, then 1F3 repeats the operation
with input a, overwriting R5:

```
R5 = (2*(a-1))&255
Q = FE
```

The first input f has no surviving effect on R5, but it affects earlier
transient arithmetic. 1F5's R3 difference is overwritten by 1F6's zero R1 copy.
1F7 calls 238, which eventually copies R0=FF into Q.

1F8 masks Q with an independent external byte and shifts the result into R0,
while shifting Q to 7F. The actual 1E9 drain then overwrites R0 with successive
Q shifts and finishes with R0=Q=0. It visits its PLP at cycles 64,66,...,78,
including the final zero iteration. 1FA calls 311 to copy zero R13 to R12.

1FB calls 240 with R0=0; its return leaves Q=0. The second mask/shift at 1FC
therefore produces zero for every external mask. The second drain has only
one PLP/BLT pass, at cycles 96–97. 1FE calls 311 again, and 1FF branches to
308 at cycle 103. The first mask, second mask and first construction input
cannot change the resulting paired component in this context.

## Rejoining preparation and exposing the component

308 calls 314. Independent h=D316 and l=D317 survive as R13=h and R4=l.
R5 still contains the component above; R6/R7 remain zero. The 370 paired call
starts at cycle 111. Let U=l+256*R5, and let i=0..3 be the global declared table
index. The four transient output bytes are:

| i | First word | Second word |
| --- | --- | --- |
| 0 or 3 | (2U) modulo 65536 | 0 |
| 1 or 2 | 0 | 0 |

Each word is exposed low byte first. The final high byte is zero in every
case, so the paired wait returns after one pass even when the first word's
high byte is nonzero. For a=128 and l=255, indices 0/3 expose FE FD 00 00.
These are ALU Y values; this experiment does not assign them to a DAC or
another physical consumer.

## Complete terminal state

All tested paths first execute 084 at cycle 146, independent of the code,
component input and masks. The terminal helpers clear R5. The global table
index also chooses both terminal store destinations: R0, R1, R2 or R3. 07C
has set R2=1, so only index two overwrites it with zero.

The complete final state is:

```
Q=0
R4=l; R13=h
R2=0 if i=2, otherwise 1
all other RAM registers zero
```

Maximum stack depth is three and final depth is zero. This distinction between
transient paired output and final retained RAM is essential: inspecting only
terminal R5 would miss the component constructed by 1F3.

## Verification

The study executes 2,048 complete 192-instruction reset cases: all 32 codes,
four global indices, and four boundary values each for a and l. The other
input bytes vary with those values; independent randomized regressions vary
all six data inputs separately and perturb the discarded inputs. Sixty-four
negative-control reset runs check the two excluded entry premises.

Each successful run checks prefix equality, the actual entry transfers, Q
writes, drain iteration cycles, both 311 calls, paired output bytes, complete
final RAM/Q, terminal timing and stack depths. Eight saved witnesses cover
small/large codes and all four paired indices; they replay byte for byte.
This is an additional coherent execution hypothesis, not a merger of
incompatible condition mappings into recovered hardware coverage.

[Runner](handler3_drains.py) and [report](results/handler3-drains/report.json).

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/handler3_drains.py
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -p 'test_*.py'
```
