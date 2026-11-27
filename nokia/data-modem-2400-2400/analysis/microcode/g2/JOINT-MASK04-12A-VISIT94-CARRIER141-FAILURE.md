# Carrier-141 gain challenge rejects the frozen visit-94 decoder

The [later-capture gate](JOINT-MASK04-12A-VISIT94-PHASE-GATE.md) passed
four fresh streams at 0.8× gain and carrier starts `133`/`135`. This
[matched challenge](joint_mask04_12a_visit94_gain07_challenge.py) freezes
that rule and capture schedule, offers two more fresh eight-byte
controller payloads at carrier start **141**, and runs the real transmit
and receive PROMs at **0.7× and 0.8×** calibrated receive gain. Within
each selector, the transmitter and receiver PC-path digests are equal
across gains; PCM and receiver traces change. None of the four modeled
PCM streams clips.

| Gain | Selector | New states relative to prior mode-1 labels | Gate-active state | Old veto errors | Visit-94 gate errors |
| ---: | --- | --- | --- | ---: | ---: |
| 0.7× | call `40` | `0A 4A 53 5C` | `0D` ×7 | 21/64 | **19/64** |
| 0.7× | answer `60` | `0A 4A 53 5C` | `0D` ×11 | 18/64 | **22/64** |
| 0.8× | call `40` | `0A 0E 4A` | none | 6/64 | **6/64** |
| 0.8× | answer `60` | `0A 0E 4A` | none | 14/64 | **14/64** |

The modeled 8251 handoff emits bytes without overruns or errors, but
none of its four line-byte streams or executed 8031 decoded payloads
matches the offered data. The independent reference receiver misses
only one call dibit and no answer dibits at each gain. This is a
negative, active holdout for the frozen external gate, not a clipping
artifact or a transmitter change.

The [joined phase graph](joint_mask04_12a_visit94_gain07_graph_audit.py)
has zero internal conflicts across sixteen expanded real-PROM streams
and 18 observed seven-bit states, including the held-`81` control below.
Anchored at prior state `49` phase 2, the candidate has wrong phases at
`0A`, `1C`, `4A` and `53`; the inferred phases are 2, 1, 2 and 3,
respectively. Visit-`94` Y6 never splits a seven-bit state **within
those sixteen streams**. The
same graph assigns `0D` phase 0, versus phase 1 in the older passing
mode-1 graph.

To test that discrepancy, the [older answer replay](joint_mask04_12a_visit94_old0d_replay.py)
re-executes both saved phase-112 answer mode fixtures with visit `94`
captured. It preserves their original zero-error decisions. Held `81`
has 43 occurrences of `0D`: 39 with later Y6=1 and four with Y6=0.
The `81→A1` edge fixture has 32 occurrences, all with later Y6=1.
Applying the frozen visit-94 gate gives **seven errors in each older
fixture** and wrong line/controller bytes. Thus the later bit alone
does not safely distinguish all `0D` uses.

The [matched mode control](joint_mask04_12a_visit94_mode81_control.py)
then holds `D3EB=81` on the **same** carrier-141 0.7× PCM and payloads.
The transmitter, raw-code and PCM hashes match the switched-`81→A1`
cases. Holding `81` changes the receive states but still yields
**15 call and 23 answer errors**, wrong line/controller bytes, and
`0D` with later Y6=1 in both selectors. The joined graph still
requires `0D` phase 0. The proposed direct mode byte alone therefore
does not repair the decoder or explain the old-versus-new `0D` phase
difference under this fixture.

This failure leaves C3 and G2 active. Next test a carrier/timing-history
capture or another independently constrained receive state source
on the matched carrier-141 and older phase-112 cases.
Keep all DAC/line, ADC, latch, gate, clock and serial nets as labelled
assumptions. The [challenge report](results/joint-mask04-12a-visit94-gain07-challenge.json),
[phase graph](results/joint-mask04-12a-visit94-gain07-graph-audit.json)
and [older `0D` replay](results/joint-mask04-12a-visit94-old0d-replay.json)
and [held-mode control](results/joint-mask04-12a-visit94-mode81-control.json)
retain the trace, state and handoff evidence.
