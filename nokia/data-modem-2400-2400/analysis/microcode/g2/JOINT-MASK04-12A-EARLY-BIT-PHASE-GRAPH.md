# An early receive bit resolves the observed phase-state conflict

The [carrier-141 failure](JOINT-MASK04-12A-VISIT94-CARRIER141-FAILURE.md)
showed that the frozen seven-bit state plus visit-`94` Y6 cannot assign
one phase to older and newer `0D` captures. The [full older replay](joint_mask04_12a_visit94_old0d_replay.py)
now saves all five Y/row visits for both passing phase-112 answer
streams. The [signature audit](joint_mask04_12a_0d_signature_audit.py)
compares their `0D` occurrences with carrier-141 streams under the same
held-`81` and switched-`81→A1` input fixtures:

| Input at `0D` | Older phase-112 occurrences | Newer carrier-141 occurrences |
| --- | ---: | ---: |
| Held `81` | 43 | 18 |
| `81→A1` | 32 | 18 |

In **both** mode comparisons, first `3F8` Y4 at visit `46` is 0 in
every older `0D` and 1 in every newer `0D`. Row-0 Y1 at visit `46`
is 1 in every older `0D` and 0 in every newer `0D`. The proposed
visit-`94` Y6 is not a reliable separator: held-`81` older `0D`
contains both values, and the switched-mode older and newer cases
all have Y6=1.

The [feature graph](joint_mask04_12a_0d_feature_graph.py) joins **18
saved real-PROM streams**, 1,170 symbols and 1,152 known dibit
transitions under the same phase convention. It screens early bits as
additional captured state, without fitting a Boolean gate:

| Captured state | Distinct codes | Directed graph conflicts | Components |
| --- | ---: | ---: | ---: |
| Original seven bits | 21 | 116 | 1 |
| Seven bits + first Y4 | 24 | **0** | 1 |
| Seven bits + row-0 Y1 | 24 | **0** | 1 |
| Seven bits + visit-`94` Y6 | 26 | 16 | 1 |
| Seven bits + both early bits | 24 | **0** | 1 |

The two early bits separate the same observed state collisions in this
set; combining them adds no observed state. Row-0 Y1 is identical at
visits `46` and `47` in **all 1,170 symbols**, so an assumed third U12
flip-flop could capture it on the already modeled visit-`47` clock.
First Y4 instead requires a fourth U14 latch at visit `46`, plus a
copy to another U12 flip-flop before U14's later paired enable reopens.
Both are package-capacity hypotheses, not identified Nokia nets.

Zero graph conflicts are **development evidence**, since these same
streams selected the features. They do not supply a complete Boolean
phase circuit, a physical latch/serial route or an unseen-data pass.
Freeze one early-bit candidate and test fresh controller payloads,
carrier phase and receive gain; record any new state that lacks a
phase label rather than silently fitting it. The [signature report](results/joint-mask04-12a-0d-signature-audit.json)
and [graph report](results/joint-mask04-12a-0d-feature-graph.json)
retain the exact values, graph labels and source hashes. C3 and G2
remain open.
