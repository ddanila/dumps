# Actual flags admit the 0FD–0FF continuation

*Runs under the [shared assumptions](ASSUMPTIONS.md).*

**0FD–0FF now have clean integrated reset witnesses under fitted_swapped.**
A raw-bit clause that makes the 0FC identical-word class conditional permits
255 runs through the continuation. This does not contradict the
[alias obstruction](GATE-ALIASES.md): the conservative graph still has possible
stack-underflow paths, while the tested actual flags take clean paths.

## Explicit diagnostic gate

The added clause is:

```json
["10.0", "!10.4", "10.7", "11.0"]
```

It is appended to the previous four-clause optional gate. It makes exactly
0FC, 216, 219, 280 and 28D newly conditional. A targeted search for an OR
clause isolating that class finds no one-, two- or three-literal solution and
three four-literal solutions. It tests 32, 496, 4,960 and 35,960 candidates at
those respective sizes. This is a minimal clause within that search form,
not a recovered physical signal or a general Boolean minimization result.

The resulting conservative graph reaches 1,020 used words, leaving 2DF
outside. It still reports possible stack underflows at 220 and 295. The
scenario is explicitly diagnostic; the default mapping/scenario is unchanged.

## Matched reset sweep

The experiment fixes dispatch index 3 and compares the previous and extended
gates for all six retained mappings and all 256 default read bytes. RAM/Q
start at zero; reads at 117/106 supply D then zero. There are 3,072 runs,
each bounded at 256 cycles. **All are clean and terminate at 084.**

Only fitted_swapped changes behavior between the gates. With the extension,
it reaches 0FD, 0FE and 0FF at every D except 01: 255 cases. All those cases
have Q=0 at 0FB, and 0FA produces FF from R2. The D=FF trace records an actual
nonzero copy into R0 before entering the continuation.

The other mappings supply useful limits on this observation:

- q1 visits the relaxed alias at 28D for D=00 and D=80. In both cases,
  the preceding zero flag is clear, so it still branches and its trace is
  unchanged.
- q2, q3, q4 and fitted_original visit none of the relaxed alias sites in
  this particular sweep.
- No run visits aliases 216, 219 or 280. In particular, the failure route
  through 219 from the conservative graph has not been tested away.

These results establish actual entry into the continuation, not global safety
of the gate across dispatch values, arbitrary time-varying inputs or all
reachable states. The previously recorded underflow witnesses remain relevant.

## What 0FA–0FF does under fitted_swapped

| Address | Operation and control |
| --- | --- |
| 0FA | Copy R2 into R0 |
| 0FB | Expose Q, setting its zero flag |
| 0FC | Expose `~(R7 xor Q)`; branch to 078 if preceding Q was nonzero |
| 0FD | Expose `~R15 & R0`; fixed-false select 6 falls through |
| 0FE | Expose R0 |
| 0FF | Expose `~(R7 xor Q)`; unconditionally branch to 07B |

All arithmetic is byte-wide. Only 0FA writes RAM; Q is preserved throughout.
No instruction in this interval selects an external D operand. With Q=0, the
last XNOR simplifies to the complement of R7.

In the D=FF reset witness, 0FA copies FF into R0 and 0FB produces zero.
The extended gate makes 0FC test that actual zero flag and fall through.
0FD, 0FE and 0FF each expose FF, then execution branches to 07B and eventually
reaches 084. Select 6 remains the declared constant-zero stub, so the branch
from 0FD to 2D9 is not taken in this scenario. Physical condition wiring and
external consumers of the transient outputs remain unidentified.

## Local checks

`zero_q_continuation_study.py` checks 131,072 local cases with the actual
Am2901 and X8X02 models:

- All 65,536 Q/R2 pairs, with R7 set by a bijection of R2, cover every Q/R7
  pair for the XNOR. Exactly 256 cases have Q=0 and reach 07B; the other
  65,280 reach 078.
- All 65,536 R2/R15 pairs with Q=0 check the mask in the continuation.
  Every case reaches 07B.

Every case checks the full final RAM and Q, all ALU results in the interval,
and balanced stack activity. The only RAM change is R0 becoming old R2.
These local states are not all claimed reachable from reset.

Across the accumulated named hypotheses, 21 of the 22 words outside the
default graph now have integrated reset witnesses. The remaining word is
2DF. This union combines different mappings and scenarios; it does not
establish a single recovered hardware model or complete the broader plan.

## Reproduce

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/alias_runtime_study.py
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/zero_q_continuation_study.py
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/program_reading.py
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -p 'test_*.py'
```

The [runtime report](results/alias-runtime-study/report.json) records the
minimal-clause search, graph failures, all matched cases, preceding flag events
and 12 complete FF witnesses. The
[local report](results/zero-q-continuation-study/report.json) records the
exhaustive domains, representative paths and source hashes. The default
listing retains its original unresolved-entry labels.
