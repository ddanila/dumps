# Separated source fields and a shift-until-zero routine

*Runs under the [shared assumptions](ASSUMPTIONS.md).*

The earlier rotation candidates depended on Q=0, which the
[caller study](CALLER-STATES.md) disproved for some nonzero-input paths. A
broader source-bit search finds four layouts whose table arithmetic is
independent of Q. They also provide a consistent local interpretation of 1E9
as **shift Q right until zero**, under an explicit condition hypothesis.
These are alternative decodes, not recovered physical wiring.

## What changed

The previous search restricted source controls to contiguous bit windows.
This search considers all 2,688 ordered three-bit assignments and polarity
masks over the same eight available bits. Four survive the declared source
constraints at 379, 3C5, 1E9 and 1EA:

| Variant | I0 | I1 | I2 |
| --- | --- | --- | --- |
| 1 | 17.5 | !17.3 | 18.6 |
| 2 | 17.5 | 18.2 | 18.6 |
| 3 | 17.5 | 18.3 | 18.6 |
| 4 | 17.5 | 18.4 | 18.6 |

All use function bits `10.2,10.3,!10.0` and destination bits
`11.7,11.6,11.5`, LSB first. The function assignment swaps the low two function
bits from the previous candidates. Source 4 (0,A), rather than source 0 (A,Q),
lets the second table family copy or negate A independently of Q. Source 1
(A,B) supplies the first family. Registers and carry use the previous explicit
hypotheses. This is a targeted search for a mathematical interpretation; it
does not establish that interpretation by itself.

## Tentative routine meanings

- **3C5 and 3DA: paired quarter-turn transform.** Four entries give (X,Y),
  (−Y,X), (−X,−Y), (Y,−X), modulo 65536, without a Q=0 precondition.
- **379, 392 and 3AB: paired add/subtract and permute.** Their virtual outputs
  use A+B and A−B; the older candidate used B−A. Physical output enables and
  addresses remain unidentified.
- **1E9–1EB: shift-until-zero candidate.** 1E9 computes F=Q, shifts Q right,
  and stores the same shifted value in R0. 1EA computes R0 AND Q. Consequently
  its zero flag is true precisely when the shifted Q is zero. If BLT repeats
  while that flag is false, Q drains to zero in at most eight iterations.
- **3EF: source-overlapping transform.** The earlier aliasing limitation
  remains; it is not another independent quarter-turn operation.

The loop fixture tests all 256 initial Q values for every variant. Every case
returns with balanced stack, Q=0, and exactly max(1, bit_length(initial Q))
iterations. The fixture uses zero shift fill, external D=55, and current
nonzero as the loop test. It does not prove the condition multiplexer wiring,
is not applied globally to other select-zero instructions, and contributes
nothing to reset coverage. Nor does the loop body establish what its callers
use the delay or shifting for. It is not labeled as a multiplier.

## Validation and limits

Each mapping passes 240 rotation fixtures and 360 virtual-output fixtures,
including Q values 00,01,55,80,FF and byte/sign boundary cases. This directly
checks the absence of the former Q dependency for the tested tables.

The 256 short reset-path sensitivity runs (four mappings × four D profiles ×
16 seeds) complete cleanly. The caller study also runs against all four new
mappings: the observed rotation calls still have zero source pairs in these
profiles, so their agreement is inconclusive. Nonzero fixture checks remain
the substantive arithmetic evidence, and those identities were search targets.

Four additional million-cycle integrations use seed 11 and external D=55.
Their saved traces and summaries allow inspection under nonzero external input;
clean execution does not establish useful modem behavior. Control-flow coverage
is still governed by scenario indices and conditions. The 90% target and
physical sine-ROM/DAC/controller interpretation remain unmet.

The functional/assumption suite passes 35 tests, including all-byte local loop
termination and nonzero-Q table arithmetic. Historical studies remain intact.

## Reproduction

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/independent_study.py --integrated-cycles 1000000
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/caller_study.py \
  --mapping-dir nokia/data-modem-2400-2400/analysis/microcode/assumed/results/independent-study \
  --out /tmp/nokia-independent-callers
```

The search accepts `--out`. [Configuration](independent-search.json) records
source/function/loop assumptions. [Search](results/independent-study/search.json),
[arithmetic](results/independent-study/arithmetic-1.json),
[loop cases](results/independent-study/loop-1.json),
[short runs](results/independent-study/summary.json),
[callers](results/independent-study/callers/summary.json), and
[million-cycle runs](results/independent-study/integration.json) preserve evidence.
Each mapping has a full 1024-word listing, for example
[variant 1](results/independent-study/variant-1.csv).
