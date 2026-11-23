# A three-bit gate extension and reset entry into the adjustment selector

An additional raw-bit clause exposes five more used words without structural
stack errors: 256, 257 and 2DC–2DE. Actual q2 reset runs reach all five using
logged input stubs and real datapath flags. The optional graph now reaches
1,016 of 1,021 used words under this extension; the default graph is unchanged.

## Bounded structural search

`three_bit_gate_study.py` starts with the previously studied composed BRT gate.
It appends one OR clause of three signed bits from distinct physical PROM
bits, ANDed with the existing clauses. All 39,680 such clauses are evaluated.
They produce 1,264 distinct sets of newly conditional BRT addresses.

| Candidate result | Clauses |
| --- | ---: |
| Clean, no new words | 24,442 |
| Clean, five new words | 6 |
| Graph exceptions | 15,232 |

All six improving clauses add the same five words. All 15 pairs of improving
classes are also clean, but add no further words. The selected single clause
relaxes the fewest additional BRT addresses:

```json
["!10.1", "!10.3", "!10.7"]
```

It makes 15F, 255 and 2CA conditional in addition to the existing gate's sites.
These three bits belong to the branch-address field. This remains a
structural correlation, not a recovered physical control signal. The search
does not claim optimality over larger Boolean expressions or other decodes.

The script verifies exact graph equality between its analysis predicate and
the existing runtime gate mechanism, then replays five shortest reset paths
through the actual X8X02 model. Branch targets, calls and dispatch tables are
unchanged. The five remaining structurally disconnected words are 0FD–0FF,
258 and 2DF. The gated scenario is saved separately; no default is promoted.

## Matched integrated experiment

`adjustment_entry_study.py` uses q2 with global dispatch index 12 and the
existing Q-index source at 26F. All RAM/Q start at zero. The default read is
01, with the established early zero replies at 117/106. A read of 03 at 2A8
loads Q=3 and selects the 230 path through 26F.

The experiment varies the read at 235 over all 256 bytes. That instruction
adds the byte to Q, so the resulting q spans every byte. Two input families
then exercise 251:

- **Fixed read:** 251 reads 01, so it writes R0=q+1 modulo 256.
- **Zero sum:** 251 reads −q modulo 256, so it writes R0=0 for every q.

Each family is run with the previous optional gate and with the extension:
256 values × 2 families × 2 gates = 1,024 runs. The overlap between the
families is retained as a matched case. Every run is clean and reaches 084
within 256 cycles. These PC-keyed reads are diagnostic stubs, not identified
physical channels. No flags or stack entries are injected.

| Family, gate | Runs entering 256 | Runs entering 257 and 2DC–2DE |
| --- | ---: | ---: |
| Fixed read, previous gate | 0 | 0 |
| Fixed read, extension | 1 | 1 |
| Zero sum, previous gate | 0 | 0 |
| Zero sum, extension | 256 | 1 |

## Meaning of the selector under q2

251 writes R0=D+Q. 252 exposes another D+Q result without storing it, and
253 writes the complement of R1 into R3. 254 exposes R0. With the extension,
255 tests the previous zero flag, so it falls through into 256 exactly when
R0=0; otherwise it branches to 0EB.

255 itself computes XNOR(R0,Q). Given R0=0, its defined logical carry is zero
only when Q=FF. Instruction 256 tests this **preceding carry**, selecting:

- Q≠FF: branch to 2D9, whose first q2 result is R12−1.
- Q=FF: fall through to 257, then branch to 2DC, whose first q2 result is R12.

The two tails have the already studied common suffix and join at 07B. The
first result differs by one without a stored RAM/Q effect; its external
consumer remains unidentified. The new evidence establishes a reset-entry
condition for the selection, not a physical interpretation such as rounding.

The simplest witness reads FC at 235 and leaves the 251 read at 01.
Q becomes FF, 251 wraps R0 to zero, 254 produces zero, gated 255 falls through,
and 255's zero carry makes 256 choose 257→2DC. The script checks the values,
flags and branch choices for every byte in both families.

## Scope and validation

The existing three-literal gate is supported by a structural search and these
matched executions, not by traced board wiring. Reaching more words does not
prove it is the correct gate. Across the accumulated experiments, all 17
words added beyond the default graph now have integrated reset witnesses,
using explicitly different retained mappings and scenarios. That union is
not a claim that one recovered hardware model executes the complete store.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/three_bit_gate_study.py
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/adjustment_entry_study.py
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/program_reading.py
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -p 'test_*.py'
```

The [structural report](results/three-bit-gate-study/report.json) records all
mask classes, candidate counts, pair comparisons, five sequencer witnesses
and source hashes. The [runtime report](results/adjustment-entry-study/report.json)
records all 1,024 cases and 12 complete traces. Both studies reproduce exactly.
