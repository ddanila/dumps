# The direct receive loop has only a two-word RAM carryover after ADC selection

The [full-loop scan](joint_mask04_receive_history_scan.py) runs five legal
eight-dibit waveforms through the same real-PROM mask04 receive fixture:
one payload at 0°, 45° and 90° carrier starts, and a second payload at
0° and 45°. Each run executes 96,047 words and selects 3,000 ADC bytes.
The independent reference receiver decodes each waveform. The scan checks
14,990 complete 32-word ADC visits after excluding the first visit of
each run, where the preceding sample is undefined.

For each word offset it groups executed Y, Q and all sixteen modeled
Am2901 RAM bytes by the **current** ADC high nibble, then by the
**previous/current** nibble pair. The five traces jointly cover all
sixteen current nibbles and 131 distinct adjacent pairs. Their PC paths
and 32-word schedules agree. The 0° first-payload trace digest matches
the earlier varying-waveform baseline.

| Site after `3F8` selection | Y conflicts by current nibble | Q conflicts | RAM conflicts | RAM bytes varying with previous nibble |
| --- | ---: | ---: | ---: | --- |
| Offset 0, `3F8` | 0 | 0 | 16/16 | R12, R13 |
| Offset 1, `3F9` | 0 | 0 | 16/16 | R13 |
| Offset 2, `3FA` through offset 31 | 0 | 0 | 0 | none |

No site has more than one Y, Q or RAM value for the same observed
previous/current nibble pair. This makes the transient exact in the
tested fixture: the selected previous sample still affects R12/R13
for two instructions, but `3FA` erases that difference. Y and Q never
expose it after the new ADC selection. The earlier
[matched-tail pulse trace](JOINT-MASK04-RECEIVE-PULSE-CARRYOVER.md)
observed Y/Q history **before** that selection; the two results agree
when aligned to the `3F8` read rather than to the end-of-visit `3FE`
capture.

This limits the direct `D3EB=01` route. Its tested Y/Q stream is a
current-sample codebook, and its post-`3FA` RAM does not hold a separate
carrier or symbol decision. It does not rule out a clocked external
consumer of the preselection prefix, another controller mode, or a
feedback path. The next C3 test should put a photo-compatible latch
on that **preselection** interval and challenge it with legal symbol
transitions at rotated phases, or change the assumed mode/feedback and
repeat this history scan. Any candidate bit still needs a causal
controller/USART RxD route. None of those wires is established here;
C3 remains open and G2 active.

The [machine report](results/joint-mask04-receive-history-scan.json)
contains per-word conflict counts, witnesses, trace/input hashes and
the exact observed PC sequence. Reproduce from this directory with
`python3 g2/joint_mask04_receive_history_scan.py`.
