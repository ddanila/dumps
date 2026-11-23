# Expanded dispatch indices and the conditional difference tail

Actual integrated reset execution now reaches 3BD–3BF under q2 and the
optional composed BRT gate. The earlier [gate sweep](GATE-RUNTIME.md) tested
global constant dispatch indices 0–7. Table 26F has 16 entries; the
[fixed-condition paths](CONSTANT-CONDITIONS.md) suggested index 12, which
selects entry 4 at 109, entry 0 at 3A8 and entry 12 at 26F.

## Expanded reset sweep

`dispatch_range_study.py` tests all 256 constant index bytes with D in
00, 01, 02, 55, 80, FF, plus every D byte at index 12. Duplicate cases are
removed: 1,786 cases per mapping, 3,572 total. Both mappings retain actual
previous flags, defined logical carry, the optional BRT gate, combined tables,
zero initial RAM/Q and the early zero replies at 117/106. Each run lasts 256
cycles. All execute without stack or model errors.

| Mapping | Terminal at 084 | Nonterminal at bound | Visited union |
| --- | ---: | ---: | ---: |
| q2 | 1,056 | 730 | 570 |
| fitted_original | 864 | 922 | 511 |

Sixteen q2 cases reach 3BD–3BF: D=01 and indices 12+16k, k=0..15.
All terminate at 084. At index 12, D=01 is the only byte to reach this tail
or terminate within the bound; the other 255 q2 cases do neither. No tested
fitted_original case enters the new tail. Nonterminal results are not proofs
of infinite execution.

The q2 index-12 witness dispatches 109→10E, 3A8→3AB and 26F→2CB.
It then takes 2CE→204, continues through 208 with its fixed false input,
and eventually reaches 3BB. There R0=FF and R5=00, so the subtraction
R5−R0−1 writes zero to R5. That zero flag makes gated 3BC fall through to
3BD. At this point Q=00. The tail executes 3BD, 3BE, 3BF and falls into 3C0;
the transform wrapper returns through the existing live stack and execution
ultimately reaches 084. No return addresses or branch outcomes are injected.

Across this sweep and the preceding gate sweep, integrated reset execution
has reached seven of the 12 graph-added words: 0FA, 2D9–2DB and 3BD–3BF.
287–28A and 2CF remain unvisited in these runs. The larger union is evidence
under explicit stubs, not a physical dispatch-source identification. Sampling
all byte indices does not exhaust combinations of independently varying
indices at different call sites or every input-byte/index pair.

## What 3BC–3BF does

The decoded fields for these four words are identical under q2 and
fitted_original. `conditional_tail_study.py` checks every R0/Q pair using the
actual Am2901 and X8X02 models. This is a local experiment with previous zero
set at entry to 3BC, the condition supplied by 3BB in the reset witness.
No RAM or Q value changes anywhere in this tail.

Let A=R0 and q=Q; arithmetic is modulo 256:

- 3BC exposes `~(A xor q)` and, given the entry premise, falls through.
- 3BD exposes `q−A`. Its skip uses the previous result from 3BC: it skips
  3BE unless q is the bitwise complement of A.
- When executed, 3BE exposes `q−A−1`.
- Gated 3BF tests the preceding arithmetic result. Nonzero branches to 287;
  zero falls through to 3C0. Its own ALU result is `A & q`.

Thus 3C0 is selected for the 256 pairs with q=A, plus (A,q)=(7F,80) and
(FF,00). The other 65,278 pairs branch to 287. These counts, instruction paths,
ALU expressions, unchanged RAM/Q and balanced stack are exhaustively checked.
The reset witness exercises the (FF,00) exception: transient results are
00 at 3BC, 01 at 3BD, 00 at 3BE and 00 at 3BF.

The external consumer of these transient values is unidentified. The optional
BRT gate is still a hypothesis based on address bits; default reachability
labels remain unchanged. This local rule does not establish that every tested
R0/Q pair is reachable from reset.

## Reproduce

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/dispatch_range_study.py
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/conditional_tail_study.py
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/program_reading.py
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -p 'test_*.py'
```

The [reset report](results/dispatch-range-study/report.json) records all cases,
dispatch sequences, digests, source hashes and four full runtime witnesses.
The [tail report](results/conditional-tail-study/report.json) records the
exhaustive local counts, digest, representative paths and source hashes.
