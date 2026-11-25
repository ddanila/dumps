# A candidate upper instruction connection makes the ADC upper nibble observable

The previous [full ADC-code run](LOWER-I-D3F8-FULL-ADC.md) offered real
8-bit sample codes but found identical traces after masking away bits 4–7.
At D3F8 its **upper Am2901 instruction is `FC`**, whose low operand-select
bits choose an internal source rather than external D. The upper-slice
instruction bit order is an untraced U17/U18 PROM-to-latch-to-U8 hypothesis.
The [upper-D route experiment](lower_i_d3f8_upper_d_route.py) therefore
changes one upper instruction source at a time while keeping the lower
mapping, inverted previous-sign condition, Q=5, held ADC samples and real
PROMs fixed.

Four bounded U17/U18 source alternatives—U8 I0 or I1 from U17 bit 6 or U18
bit 1—each reach 59 D3F8 visits in a 512-cycle diagnostic and produce a
different trace for held D=`04` versus `14`. The detailed follow-up uses
the closest source change, **U8 I0 from U17 bit 5 to U17 bit 6**. At D3F8
this changes the upper instruction from `FC` to `FD`; `FD` selects the
external D operand in the upper slice. That connection is **not traced** on
the Nokia board. It is one explicit photo-compatible bit-order hypothesis
inside the existing U17/U18 upper-control bundle.

Under this source change, six repeated-pattern and four seeded nonperiodic
reference streams each offer **128 held complementary ADC samples**, reach
all **24,000 D3F8 visits**, make **48,003 selected ROM reads**, avoid
`1E9/1EA` and end at `3F8`. The independent reference receiver recovers
each stimulus, and all ten candidate real-PROM runs have distinct trace
digests. These long runs establish sustained execution for the tested
fixtures; they do not identify a receive decision.

The decisive control compares each full complementary code with the **same
low nibble and zeroed high nibble** over 32 samples. All 6,000 D3F8 bytes
are selected by the ALU in both cases, and the PC sequences match:

| Dibit pattern | Upper instruction | Different state boundaries / 6,000 | Different selected ROM addresses | Different Y at `3F8` / `3F9` / `3FA` |
| --- | --- | ---: | ---: | --- |
| `0,1,3,2` | Baseline `FC` | 0 | 0 | 0 / 0 / 0 |
| `0,1,3,2` | Candidate `FD` | 5,812 | 11,368 | 5,739 / 5,391 / 5,434 |
| `0,0,0,0` | Baseline `FC` | 0 | 0 | 0 / 0 / 0 |
| `0,0,0,0` | Candidate `FD` | 5,812 | 11,458 | 5,807 / 5,583 / 5,413 |

The state boundary includes RAM, Q, ALU, next PC and stack. The change in
later ROM addresses shows that upper-byte input can alter retained modeled
state and subsequent table addressing under this mapping; it is more than
a direct display of the current ADC byte. The [saved report](results/lower-i-d3f8-upper-d-route.json)
contains exact source substitutions, visit counts, trace digests and source
hashes.

This restores **conditional upper-nibble sensitivity** alongside the
previous lower-nibble sensitivity, not a proven Nokia receiver. The upper
instruction wire, ADC bus bit order and enables,
sample clock, condition source and output route remain untraced. No decoded
dibit or USART-01 RxD transition has been identified. The next discriminating
test is to search the upper-sensitive run for a symbol decision that
generalizes to the nonperiodic streams, then constrain its physical output
route.
