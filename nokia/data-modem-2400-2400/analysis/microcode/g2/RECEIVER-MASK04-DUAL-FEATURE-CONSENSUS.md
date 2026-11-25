# Two executed capture features cover the held-out 13-angle receive stream

The [feature audit](RECEIVER-MASK04-TWO-VISIT-TRANSITIONS.md) found two
four-bit subsets of executed `3F8` Y at ADC visits 47 and 94 that have no
contradictory dibit labels in the inspected development traces. The
primary subset uses Y6/Y7 at both visits. Its
[cubic extension](RECEIVER-MASK04-CUBIC-TRANSITION.md) leaves one unknown
held-out decision, transition `3C`. The alternative subset uses Y5/Y6/Y7
at visit 47 and Y7 at visit 94. It has 91 development transition keys,
but no degree-three Boolean relation fits all of them, so this experiment
uses its frozen lookup without extrapolating unknown keys.

The [fresh feature comparison](receiver_mask04_feature_choice.py) executes
four new 576,047-instruction real-PROM streams with data seed `D2A9`.
Neither readout makes a wrong decision. The primary cubic readout leaves
one of 188 decisions unknown, at 165°; the alternative lookup leaves four
unknown, at 45° and 75°. These gaps occur in different angle cases, so
they are complementary under this fixture.

The [consensus replay](receiver_mask04_dual_feature_consensus.py) then
re-executes all 13 held-out 0°–180° streams from the original transition
test. Every trace and ADC hash matches the saved PROM run. It emits a
dibit when both readouts know and agree or when only one knows; it emits
unknown on a disagreement or two missing values. Neither held-out dibit
answer nor the fresh `D2A9` answers enter either development table.

| Held-out real-PROM readout, 13 angles | Decisions | Wrong | Unknown |
| --- | ---: | ---: | ---: |
| Primary four-bit lookup plus forced cubic labels | 611 | 0 | 1 |
| Alternative four-bit lookup | 611 | 0 | 5 |
| **Conservative consensus** | **611** | **0** | **0** |

Both readouts give a known label at 605 decisions and disagree at **none**.
For the primary unknown `3C` at 165°, symbol 42, the alternative key is
`69`; its frozen development label is dibit 0, matching the held-out
reference. The report retains the exact symbol, keys, per-angle scores,
trace hashes and source hashes. The four-case `D2A9` comparison also has
no errors, and its per-angle gaps are disjoint, but the consensus rule was
chosen after inspecting that comparison; the 13-angle replay is the
direct scored consensus test.

This is evidence for an information-preserving **candidate receive
readout**, not an identified Nokia phase tracker or a C3 pass. It needs
five `3F8` Y bits across two symbol-relative visits, previous-state
memory, a transition lookup/logic network, serialization and an
RxD/RxC/SYNDET route. The existing photographs do not establish those
connections. The 13 rotations share one data sequence and cover only
0°–180° in 15° steps; arbitrary phase, noise, clock offset and longer
streams remain untested. Next carry a complete frozen decision stream
through the paced USART/controller receive model, with explicit latch
and sync timing, and test new phase/data cases.

Machine reports:
[four-angle comparison](results/receiver-mask04-feature-choice.json) and
[13-angle consensus](results/receiver-mask04-dual-feature-consensus.json).
Reproduce from the microcode directory with
`python3 g2/receiver_mask04_feature_choice.py` and
`python3 g2/receiver_mask04_dual_feature_consensus.py`.
