# Handler 1: wrapped byte sum and shift-loop timing

Under q3, handler 1 retains a halved, eight-bit-wrapped sum of two independently
supplied bytes in R14. Its earlier arithmetic passes through two shift wrappers
whose Q values are ultimately cleared. The input code survives separately in
R4/R15 and changes execution time. This is a coherent internal-state account,
not an identification of a modem filter, physical sample, or DAC write.

## Diagnostic reset contract

Use the [handler timing](HANDLER-TIMING.md) previous-flag scenario with Q-based
109 dispatch, later constant dispatch index 2, early `[1,0]` replies at
117/106, and default external D=1. Two reset reads sum to the input code
`c=1,9,...,249`; its low three bits select handler 148 at cycle 41.
Initial RAM/Q are zero and all calls use the real four-entry stack.

Independently supply `u` at 167 and `v` at 16A. The complete final state at
terminal 084 is Q=0, all RAM zero except:

| Register | Final value |
| --- | --- |
| R4 | c+1 |
| R12 | 1 |
| R14 | `((u+v)&255)>>1` |
| R15 | `(c+3)&255` |

The sum wraps **before** the right shift. For example, 128+128 produces zero,
while 255+255 produces 127. The arithmetic therefore discards the ninth-bit
carry; it is not the ordinary unsigned average `(u+v)>>1`.

## Preparation and surviving values

148 loads R5 from D+Q. 149–14C repeatedly overwrite R0 with D+Q, and
14D–14E leave R12=c−1. The small 24F–250 helper loads Q from R12+R0;
the first call therefore supplies `2*c mod 256` to wrapper 248.

With reset R7=0, each of the wrapper's two right-shift calls takes the short
path through 29D and shifts Q once. Its 187 left-shift loop then clears Q.
On return to 151, Q=0 and R0=1. The following masked write clears R0, and
154–155 replace R12 with FE. The second 24F call consequently loads Q=FE;
the same wrapper shifts twice to 3F before its left drain clears Q again.
This second left drain always executes nine iterations.

The continuation at 2E6–2EB overwrites R12 with the default external byte 1.
Thus the earlier R12 difference does not survive in that register. It also
prepares R0=1. At 164, subtraction of default D=1 clears R3.

167 loads Q=u. 168 leaves it unchanged; 169 copies it. At 16A the ALU forms
`(u+v)&FF`, writes its right shift into R14, and independently right-shifts
Q. The following 1E9 call drains Q to zero. 16C–170 then clear/reload Q=0
and call the same drain once more. Neither drain changes R14.

172 copies R2=1 into R15. 173 masks this with R3=0 into Q, and 174 adds
R4 plus R15 plus one, giving R15=c+3. The continuation at 180–186 exposes
several transient arithmetic results, including an R14 use at 184, but
preserves R14. It reaches 0E9/0EA and the terminal tail; its register-2 stores
clear the temporary R2 values. No physical consumer of the transient results
has been identified.

## Instruction count

For the first wrapper, let `z=((2*c)&255)>>2`. The 187 loop executes one
iteration if z=0; otherwise it executes `9-trailing_zero_bits(z)` iterations.
Call this count n. Under previous-zero timing it includes the final iteration
whose pre-shift value is already zero.

The later right drain executes `bit_length(u>>1)+1` iterations. Its following
zero-input drain executes once. First execution of 084 is therefore at cycle

```
195 + 2*n + 2*bit_length(u>>1)
```

from reset. It does not depend on v. The tested paths first reach 084 between
cycles 197 and 223. These are modeled microinstruction counts, not a recovered
sample clock or rate.

## Verification and scope

The actual 167–16A instructions are checked locally for all 65,536 u/v pairs,
starting with nonzero unrelated RAM to expose unintended writes. The check
compares full RAM, Q, sum and carry against the formula; 32,640 pairs wrap.

The main integrated runner also executes 2,264 complete zero-reset cases:
all 256 u values at code 1 with four v values, and ten u boundaries at each
of the other 31 codes with the same four v values. Those boundaries cover
all drain lengths. These are not claimed as all 2,097,152 code/u/v combinations.
Each tested run checks full final RAM/Q, intermediate states, all drain counts,
terminal timing, stack balance, and full-state terminal recurrence. Eight
complete witnesses retain the extreme sum and timing cases.

The interpretation uses q3, previous flags, zero-fill shifts and the declared
PC-keyed inputs. Selector 6 is false and selector 5 is true, so the alternative
178–17F continuation is outside this contract. Other input sites retain D=1;
changing them can invalidate the formulas. The controller protocol, output
strobes and broader modem function remain unresolved.

[Configuration](handler1-study.json), [runner](handler1_study.py),
[report and witnesses](results/handler1-study/report.json).

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/handler1_study.py
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -p 'test_*.py'
```
