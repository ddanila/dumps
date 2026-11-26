# Frozen six-bit receive rule at a second carrier start

The [frozen six-bit holdout](JOINT-MASK04-12A-FROZEN-SIXTH-HOLDOUT.md)
recovered a third eight-byte payload in each selector mode at running
Am2901 R1 offset 32 and 75%, 100% and 125% of the fixed zero-run gain.
This replay keeps those payloads, the 91-key transition table, Y-bit
feature, DAC bus, line filter, ADC visits and modeled serial handoff
fixed. It changes only the one-time R1 offset at mute start to **96**.
That offset is a diagnostic carrier-phase intervention, not a verified
board input.

| Selector | Payload | Receiver decisions at 75%, 100%, 125% | Recovered line bytes | Aligned modeled 8251/8031 handoff |
| --- | --- | --- | --- | --- |
| `40` | `0F 72 B5 C8 31 E6 4A 9D` | 64/64 exact at each level | eight exact at each level | eight exact source bytes; no errors or overruns |
| `60` | `A6 19 F0 4D 83 2B C5 78` | 64/64 exact at each level | eight exact at each level | eight exact source bytes; no errors or overruns |

All six real-PROM Tx→line→Rx traces differ from the offset-32 traces
in raw output, filtered PCM, receiver execution and transition-key
sequence. No receive label was fitted on these runs. All observed keys
are nevertheless among the same 91 development keys, so this tests a
second phase start without establishing behavior for unseen keys. The
independent fixed-carrier reference receiver has one wrong dibit in
each answer-mode run; the DSC-derived six-bit rule has none.

The [machine report](results/joint-mask04-12a-frozen-sixth-phase96.json)
contains the captured Y values, transition keys, decisions, trace
digests, serial handoff and source hashes. Reproduce with:

```sh
python3 g2/joint_mask04_12a_frozen_sixth_phase96.py
```

This remains a conditional explanation. The ADC capture clocks,
six-bit storage and transition logic, converter buses, analog route,
SYNDET and serial wiring are photo-compatible assumptions. C2/C3/G2
remain open. Next challenge the frozen rule with a shifted capture
edge or a third carrier start and seek a photo-compatible circuit that
computes the decision without a table trained on known payload labels.
