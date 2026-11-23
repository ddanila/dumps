# Global branch-address bit alternatives

Changing B0 alone does not explain the remaining disconnected fragments while
preserving the current control-flow structure. The existing B0 = 11.0 and
B9 = 18.7 are the only candidates in their respective sweeps that retain
999 reachable used words without graph exceptions. This is evidence against
a simple global single-bit correction, conditional on the other assumptions.
It does not establish the physical wiring.

## Experiment

The baseline is the combined local-case scenario from [LOCAL-CASES.md](LOCAL-CASES.md).
For each of B0 and B9, replace that bit with each of the 32 PROM data bits,
in both polarities: 64 candidates per position, 128 total. Each sweep includes
the unchanged baseline. All other address bits, command and condition fields,
and dispatch target lists remain fixed. Repeated source bits are permitted;
the report preserves the token and changed direct transfers for each candidate.

Each candidate receives a fresh reset-started graph exploration with the real
four-entry stack limit. Both outcomes of conditional instructions are explored.
This is a structural experiment, not an integrated runtime or I/O experiment.

| Changed position | Candidates without exceptions | Their reachable used words | Candidates with exceptions |
| --- | --- | --- | --- |
| B0 | 18 | Baseline 999; 17 alternatives reach only 8 or 9 | 46 |
| B9 | 10 | Baseline 999; 9 alternatives reach only 308 | 54 |

No exploration exhausts the 500,000-state budget. None of the failing B0
candidates reaches more than 907 used words; none of the failing B9 candidates
reaches more than 653. Therefore even ignoring stack validity does not produce
a coverage improvement in this particular sweep. Small clean graphs are not
treated as better decodings merely because they avoid a failure.

## Concrete inversion counterexamples

With B0 inverted, the transfer at 003 goes to 101 instead of 100. A shortest
failure witness has 25 states, ending at the BLT at 107 with an empty logical
stack. BLT consumes a stack entry regardless of its condition. Intermediate
helper calls return normally; the final path is
104 → 113 → 114 → 115 → 116 → 105 → 107.

With B9 inverted, a shortest witness is:

`000 → 001 → 002 → 003 → 300 → 301 → 302 → 119`

The POP at 119 also has no return address. The report retains every state and
its logical stack for both witnesses, plus the exact candidate mappings.
A regression check replays both paths through the independent `X8X02` component
without injected return values or dispatch targets and confirms that the final
stack-consuming instruction has no live stack entry. The circular hardware stack may still contain
stale values; logical underflow is not necessarily an unknown-value exception.

These paths demonstrate possible failures under the graph's condition model.
They do not establish that the real board selects those condition outcomes.

## What remains open

The 22 disconnected words remain unresolved. A context-dependent branch bit,
a joint change to multiple fields, or a missing computed target family is
outside this sweep. The result narrows the next investigation: a global B0 or
B9 substitution alone is insufficient under the present dispatch assumptions.
Neither these negative results nor the baseline's coverage explains the
fragments' arithmetic purpose or physical I/O.

## Reproduce

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/branch_bit_study.py \
  --out /tmp/nokia-branch-bits
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -p 'test_*.py'
```

[Configuration](branch-bit-search.json) and [report](results/branch-bit-study/report.json)
record all candidates, graph exceptions, gained/lost addresses, target scores,
and the two failure witnesses. The report reproduces byte for byte. All 59
functional/assumption tests pass.
