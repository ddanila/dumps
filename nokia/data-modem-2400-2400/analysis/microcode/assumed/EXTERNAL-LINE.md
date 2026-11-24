# Timed external input and the handler-3 continuation

The executor now accepts a cycle-timed digital input in addition to the
existing constant external bit. This lets a scenario preserve the boot
condition and change the same external line later, without overriding a branch
at a particular PC. A reset study uses it to enter handler 3's double-preparation
and paired-wait continuation. It also explains why that continuation still
bypasses 1EF under the tested q3 assumptions.

## Scenario interface

A constant `inputs.external` value of 0 or 1 retains its previous behavior and
trace format. A timed line is explicit and carries provenance:

```json
{
  "mode": "cycle-events",
  "initial": 1,
  "events": [[40, 0]],
  "status": "stub",
  "evidence": "Diagnostic line falls at instruction cycle 40; physical pin unknown"
}
```

Place this object in `inputs.external`. Any condition selector whose source is
`external` reads this one line, then applies its normal polarity. Events take
effect on the named zero-based instruction cycle, including a condition test
on that cycle. The initial value applies before the first event; the final
value is held indefinitely. Cycles must be nonnegative integers in strictly
increasing order; values must be bits. Missing provenance, duplicate or
unsorted times, negative times and invalid values are rejected.

The schedule is indexed by instruction cycle, not PC, and does not change
unconditional-transfer rules. Each actual scheduled-line read adds an
`external_condition` trace record containing the raw value, event index,
event cycle and provenance. Index -1 identifies the initial value. Polarity
and the resulting condition test remain visible in the ordinary trace fields.
An event does not fabricate a read at a cycle where the line is not consulted.

This is a digital stimulus, not a recovered interrupt pin, clock frequency or
controller protocol. Reads and writes on other interfaces keep their existing
explicit policies.

## Future events and recurrence

A machine that revisits the same registers before a scheduled input change is
not necessarily stuck. The handler-timing classifier therefore includes the
next instruction cycle in its state key until the last event is reached. The
time component then saturates, allowing recurrence to be proved once future
line values are constant. Existing constant-input scenarios retain their
previous recurrence keys and results.

A regression test starts at real BSR 1F9, calls the 1E9/1EA loop, and supplies
an external condition that releases it at cycle 10. The BLT repeats at cycles
2, 4, 6 and 8, then exits at 10 and returns at 11. The classifier refuses to
call the eight-instruction prefix a persistent recurrence. With the same line
held low instead, the ordinary executor and classifier establish period two.
No return frame or PC is repaired in either case.

## Reset experiment

Use q3 and input codes `3,11,...,251`, selected through Q at 109. Compare the
existing matched early replies: previous flags with PLP-side replies, or
current flags with BLT-side replies. D defaults to one outside those established
reset inputs, and later table indices stay two. Selector 5 now reads the timed
external line with normal polarity; it starts high and falls once.

Across each matched baseline's first 44 cycles, selector 5 affects control
flow only at boot BRT 003 (cycle 3) and handler BRT 302 (cycle 43). The study
checks this directly against the decoded instructions. Therefore the timing
window is explained by actual instruction boundaries:

| Falling edge | Observed consequence |
| --- | --- |
| Cycle 0 or 3 | Boot takes the alternative path; these cases never reach 109 |
| After cycle 3 and by cycle 43 | Boot is preserved; 302 falls through to 303 |
| Cycle 44 or 100 | 302 already took its original branch to 319 |

The sweep tests edges 0, 3, 4, 40, 43, 44 and 100 for all 32 codes under both
timings: 448 complete 512-instruction reset runs. Before the falling edge,
every trace matches its original constant-line baseline after removing only
the new external-line read metadata. All runs are clean, execute no unused
word and respect the four-entry stack limit.

## Why the observed path excludes 1EF

On the preserved handler-3 prefix, R0=FF and Q is its nonzero input code. 302
computes their sum, whose carry is always one. In previous-flag mode, 303 tests
the inverse of that carry, so its branch to 1EF is false.

In current-flag mode, 303 tests its own OR carry. Its carry-in is one, making
its defined logical carry one under the selected ripple model regardless of
the operands. The inverted test is again false. The reset study checks the
actual 303 result and branch in every admitted case. This excludes 1EF for
these conditions; it neither annotates that unexecuted body nor proves it is
unreachable under other inputs, entry states or mappings.

## Executed continuation and result

303 falls through to the paired preparation at 304–307. Each call to 30B
clears Q and executes the short drain; each 311 call copies the prepared
register. 308 calls 314, preparing the register values used by 309's call to
370. That helper starts at cycle 74. Its declared entry 2 at 376 subtracts each
word from itself, exposes four zero bytes and returns after one pass. In
current-flag mode, 377's own R0 AND Q is also zero, permitting the same return.
This supplies actual reset context for the local [paired-wait contract](PAIR-WAIT.md).

The successful window reaches terminal 084 at cycle 109 for every tested code
under both timings. Final Q is zero. Final RAM is zero except:

| Register | Previous flags / PLP replies | Current flags / BLT replies |
| --- | ---: | ---: |
| R4, R13 | 1 | 1 |
| R6, R7 | 0 | 255 |

The R6/R7 difference was captured by the different early reply schedules; the
self-subtracting table does not erase those source registers. Terminal entry
is not a claim of an autonomous recurring sample stream or a DAC transfer.

## Artifacts

[Line policy implementation](external_line.py), [study configuration](external-line-study.json),
[runner](external_line_study.py), and [report and ten reset witnesses](results/external-line-study/report.json).
The tests cover event boundaries, invalid schedules, a delayed loop release,
recurrence safety and both boot/handler boundaries. The legacy constant-line
traces and consolidated execution audit are replayed unchanged.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/external_line_study.py
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -p 'test_*.py'
```
