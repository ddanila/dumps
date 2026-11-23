# Pairing clean contextual branch alternatives

Combining two of the [contextual branch alternatives](CONTEXT-BRANCH.md) does
not improve the best static coverage beyond 1,000 words. Some pairs do expose
the disconnected 0FD fragment, but only while losing hundreds of other words.
This narrows a possible explanation of the missing code without promoting a
new default decode.

## Search scope and results

The prior search has 500 individually exception-free candidates. Collapsing
identical changed-target sets and removing no-change cases leaves 133 distinct
alternatives. This study tests every pair from different command/selector
classes, including candidates that individually lose coverage. It skips pairs
from the same class, even if their particular changed addresses are disjoint.

| Result | Count |
| --- | ---: |
| Pairs tested | 7,489 |
| Same-class pairs excluded | 1,289 |
| Pairs with no graph exceptions | 7,301 |
| Pairs with possible exceptions | 188 |
| Clean pairs gaining any baseline-unreachable word | 514 |
| Best clean coverage | 1,000 words |

The baseline reaches 999 words. The best pair gains only 28A and loses none,
matching the single-class result. Across all clean pairs, newly reachable words
are confined to 0FD–0FF, 28A, and 2D9–2DB. No clean pair reaches the other
unresolved roots 0FA, 256, 258, 2CF, 2DF, or 3BD.

Four clean pairs expose 0FD–0FF and 2D9–2DB. Their best coverage is only 615:
six gained words and 390 lost baseline words. A representative combines:

- B9 from 11.5 for direct BRT with selector 0, redirecting several high-page
  jumps, including 2E5 and 3BC from 2FD to 0FD.
- B9 from inverted 10.2 for direct BRT with selector 7, changing 009 from 00B
  to 20B and making a different region reachable.

Neither constituent alone reaches 0FD under this scenario. The joint result
shows why the original single-class search could miss entry paths, and why
merely making one orphan fragment reachable is an insufficient model-selection
criterion. It is not evidence that these two rewires describe the board.

The graph checks all possible conditional outcomes with the existing dispatch
tables and empty initial stack. Clean constituents do not guarantee a clean
combination: 188 pairs introduce possible failures. Conversely, this search
excludes combinations in which two individually failing alternatives repair
each other. Three-class changes, same-class multi-bit changes, and different
dispatch hypotheses also remain outside its scope.

## Reproduce and inspect

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/joint_branch_study.py
```

[Configuration](joint-branch-search.json) records the scope.
[Report](results/joint-branch-study/report.json) records the source-report hash,
all 133 alternatives and equivalent bit assignments, coverage histogram, and
representatives for best coverage and most newly reached words. Both
representatives include reset paths replayed on X8X02 with exact live-stack
matching. Computed targets remain constrained to the existing scenario tables.

[Pair results](results/joint-branch-study/pairs.csv) preserve every pair's
reachable-address count, exception count, and gained/lost address ranges. Ranges
are inclusive hexadecimal. Counts for failing graphs can include unused words;
those graphs are not treated as clean coverage results.

The unit test verifies equivalent-target deduplication, rejection of same-class
pairs, and preservation of original decoded rows. Runtime mappings and the
principal annotated listing are unchanged. The full plan remains incomplete.
