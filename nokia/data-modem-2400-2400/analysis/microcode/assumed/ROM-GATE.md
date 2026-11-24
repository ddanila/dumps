# A raw-word ROM-read gate preserves the sine path, but remains ambiguous

The [sine operand experiment](SINE-OPERAND.md) selected ROM input specifically
at PC 317. A small raw-control-word predicate can replace that single-PC choice
and preserve its arithmetic result across the whole quarter-sine table. This
is a more general executable read-selection hypothesis, not recovered wiring.

## Assumed labels and exhaustive bounded search

The positive example is word 317. Negative examples are the external-sequence
sites 002, 076, 117, 106, 118, 107, 38E, 36D and 316. Those labels preserve the
existing diagnostic input protocol, including the address-setting byte at
316. They are assumptions from the constructed scenario, not measured chip
selects. No other instruction is labelled negative merely because it was not
used as a ROM input in the earlier experiment.

The search enumerates every conjunction of one, two or three literals on
distinct raw PROM bits, allowing either polarity: 64 + 1,984 + 39,680 = 41,728
predicates. All four PROMs participate; the search is not restricted to
unassigned bits. Every fitting predicate is compiled into the complete list
of qualifying control-store addresses and executed through the existing
selected-ROM input model. Thus extra activations anywhere in the program
actually affect D and are not discarded by the experiment.

There are no single-bit fits and exactly one two-bit fit:

```
11.4 = 0 AND 18.5 = 0
```

It selects 433 used words, of which 31 select D as an ALU operand under q3.
In the retained q3 mapping, 11.4 is part of the A-register field; 18.5 has no
named field owner. A bit's current assignment does not preclude an additional
control role, and absence of a named owner does not establish one.

Allowing three bits yields 137 fits in total, with 107 having no smaller
fitted literal subset. All 137 have different global activation sets, ranging
from 45 to 554 words. The two-bit result is unique only within its restricted
search size. It is not a unique Boolean explanation of the labels.

## Global execution and extra ROM reads

The two-bit gate is tested at all 65 sine phases. Each of the other 136 fits is
tested at phases 0, 32 and 64: 473 reset runs, 160 instructions each. All are
clean and reach 084 at cycle 110 with the expected first arithmetic output
`2*(ROM[100+phase]+5)` and second output 0002. The larger gates are not swept
over every phase.

For the two-bit gate at phase 32, 88 reads qualify as ROM samples over the
160-cycle run. Only four are selected as D operands:

| PC (hex) | Cycle | ROM address (hex) | Byte (decimal) | Effect |
| --- | --- | --- | --- | --- |
| 115 | 19 | 106 | 19 | Writes a transient R4 value |
| 115 | 31 | 106 | 19 | Writes that transient R4 value again |
| 317 | 45 | 120 | 90 | Supplies the surviving sine component |
| 36C | 84 | 100 | 0 | Changes downstream carry-loop arithmetic |

The two 115 values are overwritten before the table output. The later read
at 36C leaves a different internal continuation state even though the target
arithmetic bytes and terminal cycle agree. At phase 32, for example, the
two-bit gate ends with R1=FF and R3=00, while the original single-PC experiment
ends with R1=00 and R3=02. Matching the selected output does not imply complete
state equivalence.

All 137 fits pass the three tested phase boundaries, but they produce 57
different ordered sequences of selected ROM reads at phase 32. For example,
`11.3=1 AND 17.3=1 AND 18.1=0` qualifies 62 words and reads ROM operands at
315, 317 and 366 in that run. It obtains the same selected output while making
different predictions about other bus activity. The report preserves full
final states, all selected ROM read events and activation lists for comparison.

## Meaning and remaining questions

A PC-specific input fixture is no longer necessary to obtain this sine path:
a simple raw-bit read policy can do so without replacing the handshake inputs.
However, these labels and output checks do not identify a physical read-enable
signal. More complicated fitting gates survive, and the labels are not
independent hardware evidence. Neither the address latch, shared-bus selection,
DAC write-enable, nor sample clock is recovered here. The gate is confined to
explicit experiment scenarios; existing defaults are unchanged.

The next discriminating work should use other handlers and input schedules,
retaining full internal states and extra ROM reads rather than judging a gate
only by one chosen arithmetic result.

## Reproduction and checks

[Configuration](rom-gate-study.json), [runner](rom_gate_study.py), and
[report](results/rom-gate-study/report.json) retain the labels, search scope,
all fits, 473 outcomes and nine full traces. The 94-test suite checks the
bounded search result, exact extra-read events, and rejection of contradictory
labels. The experiment reproduces byte for byte. No annotation count changes.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/rom_gate_study.py --out /tmp/nokia-rom-gate
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -p 'test_*.py'
```
