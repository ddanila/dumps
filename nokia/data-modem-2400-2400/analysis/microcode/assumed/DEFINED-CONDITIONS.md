# Condition fits with defined logical flags

*Runs under the [shared assumptions](ASSUMPTIONS.md).*

Recomputing the local preparation-use witnesses with [defined logical flags](LOGIC-FLAGS.md)
admits a current-flag policy for the swapped-register interpretation. It does
not resolve the physical condition wiring or flag timing. The original-role
witness still has no current single-flag fit for selector 3, but an explicit
constant-one condition can reproduce its prescribed outcomes.

## What is fitted

The earlier local witnesses prescribe PC paths and branch outcomes. This
study keeps those paths and their external D bytes fixed while recomputing
RAM, Q, carry feedback and ALU flags using the new component mode. It then
tests each flag and polarity across both zero and marked input traces.

These are consistency constraints derived from a constructed path, not
measurements of hardware decisions. A fitted policy is subsequently replayed
in the main integrated runner without per-PC branch overrides. All eight
local replays match the recomputed paths, full RAM/Q state, carry input, ALU
results/flags and external read values exactly.

## Timing alternatives

Selector 3 illustrates the change:

| Register roles | Current single-flag fits | Previous single-flag fits | Constant fit |
| --- | --- | --- | --- |
| Original | None | NOT carry; NOT overflow | 1 |
| Swapped | NOT overflow | Zero; NOT sign; NOT carry; NOT overflow | 1 |

In the original-role traces, every selector-3 outcome is prescribed as one,
while each current flag varies somewhere in those observations. This excludes
a single current flag with fixed polarity for that selected path. It does not
exclude a constant external condition, another signal, or another path.

All observed selectors have constant outcomes within these short witnesses.
Consequently, the apparent flag fits are weak constraints: they do not prove
that the flag caused the decision. Defined flags make more alternatives
testable, rather than identifying one as correct.

Four representative policies are saved explicitly:

| Policy | Timing | Selector assignments |
| --- | --- | --- |
| Original previous | Previous | 0=NOT zero, 2=carry, 3=NOT carry, 7=zero |
| Original current with external condition | Current | 0=NOT zero, 2=carry, 3=constant one, 7=zero |
| Swapped previous | Previous | 0=NOT zero, 3=zero, 6=zero, 7=NOT zero |
| Swapped current | Current | 0=NOT zero, 3=NOT overflow, 6=zero, 7=NOT zero |

The previous policies are retained from the earlier fit. The current swapped
policy changes selector 3 to a newly available fit. The current original
policy deliberately labels selector 3 as constant, rather than falsely
presenting it as a flag match.

## Reset extension

Each policy is also applied to the previous reset scenario with its free
selector completion preserved, including selector 5=1 and dispatch index 2.
No search over those settings is performed. All eight 1,000-cycle runs reach
preparation and finish cleanly without unknown carry substitutions or unknown
flags at real condition decisions.

| Policy | Zero input: words / final PC | Marked input: words / final PC |
| --- | --- | --- |
| Original previous | 162 / 1EC | 187 / 084 |
| Original current with external condition | 189 / 084 | 189 / 084 |
| Swapped previous | 186 / 084 | 186 / 084 |
| Swapped current | 186 / 084 | 186 / 084 |

The original-role zero and marked inputs first diverge in control flow at
cycle 104 under both policies. Their first Q-drain loop behaves as follows:

| Timing | Zero input shifts | Marked input shifts | Marked Q after shifts, hex |
| --- | --- | --- | --- |
| Previous flags | 1 | 9 | 43,21,10,08,04,02,01,00,00 |
| Current flags | 1 | 8 | 43,21,10,08,04,02,01,00 |

The swapped cases exit their first drain loop after one shift for both input
patterns, and the two inputs follow the same control path in the saved runs.
The report records the first loop and input-dependent control difference
separately from final coverage/state.

The current original-role alternative lets zero input reach 084 rather than
remaining near 1EC. That is another consistent modeled execution, not evidence
that reaching the terminal loop is the hardware's correct behavior. No new
entry mechanism, output consumer, sample timing or physical I/O connection is
established. The plan remains incomplete.

## Reproduce

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/defined_condition_fit.py \
  --out /tmp/nokia-defined-conditions
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -p 'test_*.py'
```

[Configuration](defined-condition-fit.json) owns the policy choices and
limitations. The [report](results/defined-condition-fit/report.json) retains
every selector observation and candidate fit, replay results, reset summaries,
loop counts and first input-dependent branches. Eight local and eight reset
directories retain complete bounded traces and exact mappings/scenarios. All
81 result files reproduce byte for byte; all 64 functional/assumption tests
pass. Historical policies and artifacts are unchanged.
