# Raw-bit-controlled branch address mux search

*Runs under the [shared assumptions](ASSUMPTIONS.md).*

A single raw PROM bit selecting an alternate B0 or B9 source does not improve
the 999-word baseline graph in this bounded search. One clean alternative makes
0FA reachable, but loses 85 baseline words. This gives a concrete entry-path
counterexample without making it a preferred decode.

The previous [contextual search](CONTEXT-BRANCH.md) grouped transfers by command
and condition selector. Here the proposed control is one raw bit, with either
polarity. For every direct BSR/BRT, the rule is:

```
if gate is asserted:
    selected address bit = alternate source bit
else:
    selected address bit = baseline source bit
```

All 64 signed raw-bit gates and 64 signed alternate sources are tested at each
of B0 and B9: 8,192 candidates. No instruction-address exceptions are fitted.
The scenario's computed dispatch overrides still take precedence over encoded
targets. The other address bits, direct flag, commands, and conditions remain
unchanged.

## Results

Identical complete target substitutions are evaluated once. The 8,192 candidates
collapse to 4,129 distinct target sets, of which 632 have no graph exceptions.
Only 11 clean target sets gain any baseline-unreachable word:

- Ten gain 28A, always losing at least one baseline word. Their maximum coverage
  is 999, exchanging 28A for 1DC, 2D0, or 17F depending on the rule.
- One gains 0FA, reaches 915 words, and loses 85 baseline words.

No candidate provides a clean coverage improvement. This result does not
contradict the earlier selector-class candidate reaching 1,000 words: matching
a whole three-bit selector value is a different gate from any one raw bit.

The 0FA candidate uses gate `!10.0`, alternate source `!10.1`, and changes B0.
It changes 51 direct-transfer targets, including 2CA from 0FB to 0FA. A path
from reset through this changed jump can be replayed on the sequencer. However,
the rule also bypasses or disconnects substantial existing code.

Both gate and alternate source already belong to the baseline branch address:
10.0 supplies B8 and 10.1 supplies B7. Thus the rule effectively replaces B0
with inverted B7 when B8 is zero. It is an address-dependent hypothesis, not
evidence that either signal is a separately decoded hardware mode control.
Condition/command bits, datapath bits, and address bits were all permitted in
the search rather than silently excluding possible overlaps.

## Evidence and limits

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/branch_mux_study.py
```

[Configuration](branch-mux-search.json) declares the gate/source search.
[Candidate table](results/branch-mux-study/candidates.csv) maps every gate and
source choice to a unique result ID. [Report](results/branch-mux-study/report.json)
records changed targets as hexadecimal `PC:target` pairs, state counts,
gained/lost address ranges, and all
exceptions for each distinct result. It includes replayed reset-to-entry
witnesses for the best representative of each clean gain pattern, 0FA and 28A.
Witnesses match next PCs and live stacks on X8X02; dispatch choices remain
constrained to the existing scenario tables.

The unit test checks gate polarity, alternate-source polarity, preservation of
the other address bits, restriction to direct transfers, and unchanged input
rows. No default mapping or annotated-listing coverage is changed.

This study tests one two-input mux at one address bit. Multi-bit gates, joint
address-bit changes, timing-dependent sources, and different dispatch tables
remain outside its scope. Possible stack failures in a graph are not measured
hardware executions. The full plan remains incomplete.
