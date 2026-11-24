# Identical-word limits and a clean entry into 258

A four-literal raw-bit gate clause isolates 257, adds entry into 258, and
raises the optional conservative graph to **1,017 of 1,021 used words**.
Matched q2 reset runs execute that new path without stack errors. The four
remaining words are 0FD–0FF and 2DF.

The same study establishes a limit on further raw-bit-only relaxation:
reaching those four words necessarily admits stack-underflow paths when
conditional flags are explored freely. This is a limitation of the
conservative graph, not a proof that real datapath flags would take those
paths or that the Nokia program is invalid.

## Why more raw bits cannot separate the problematic sites

The script first explores the superset graph in which every BRT may be
conditional. Even there, the only entries into the remaining words are:

| Word | Predecessor |
| --- | --- |
| 0FD | Fallthrough from 0FC |
| 0FE | Fallthrough from 0FD |
| 0FF | Fallthrough from 0FE |
| 2DF | Fallthrough from 2DE |

The microword at 0FC is byte-for-byte identical at five addresses:
**0FC, 216, 219, 280, 28D**. Any predicate of those raw bits must classify
all five alike. Allowing their fallthroughs introduces an empty-stack POP at
220 (and another underflow possibility at 295).

A saved reset witness takes the newly allowed fallthrough at 219 into 21A.
A computed call at 21F and its return eventually leave execution at 220 with
an empty live stack. The next POP violates the declared stack discipline.
The witness is replayed through the X8X02 model up to that failure site;
the invalid POP itself is not presented as a clean execution.

Likewise, 2DE shares its microword with **0EA, 0FF, 2DB, 30A, 334, 352, 356**.
Allowing this class to fall through produces several underflow paths. The
saved witness specifically falls from 2DE into 2DF and eventually reaches
2FF with an empty live stack, where another POP would underflow.

Both checks start from the complete previous optional graph and relax the
entire identical-word class. Additional unconditional-to-conditional
relaxations only add edges to this free-flag graph; they cannot remove the
saved failure paths. Thus no more elaborate raw-only predicate can both
admit these entries and retain a clean conservative graph while targets,
dispatch tables, calls and freely chosen flag outcomes remain unchanged.

This does **not** forbid investigating the same entries with actual datapath
flags. Flag correlations could rule out the failure witnesses, just as the
earlier q2 analysis ruled out a structurally permitted tail. Other dispatch
or call interpretations are also outside this limited argument.

## Targeted four-literal search at 257

257 has a unique raw encoding. The study enumerates the 35,960 four-literal
OR clauses that are false at that word, using four distinct physical bits.
This is a targeted search, not enumeration of all signed four-bit clauses.
There are 295 distinct relaxation masks; 782 clauses retain a clean graph.

The selected clause is:

```json
["10.0", "!10.1", "!10.4", "10.7"]
```

Appended to the previous gate, it makes only 257 newly conditional. Its mask
has 126 equivalent clauses in the targeted search. The bits are part of the
branch-address field: selection is structural, not recovered wiring.
The existing runtime gate reproduces the full analysis graph exactly.

## Reset execution through 258

`gate_reentry_study.py` repeats the preceding fixed-read adjustment experiment,
sweeping every byte read at 235 under both gate versions. The rest of the q2
scenario retains its zero reset, Q-indexed dispatch at 26F, early zero replies,
03 read at 2A8 and 01 read at 251.

All **512 runs** are clean and terminate at 084 within 256 cycles. The only
changed trace is the FC read at 235:

1. Q becomes FF; 251 wraps R0 to zero.
2. The established flags permit 255→256→257.
3. The previous gate branches from 257 to 2DC.
4. The new gate tests the actual preceding zero flag from 256 and falls
   through from 257 to 258.
5. 258 exposes Q−R0=FF without changing RAM or Q, then falls through to 259.
6. With an empty live stack, 259 makes a normal preparation call to 314.
   Execution later reaches 084 without stack errors.

The first path difference is at cycle 107, PC 257. This execution visits 259
for a second time; it does not inject a call frame to make the re-entry work.
The external consumer of the transient result at 258 remains unknown.

## Validation and reproduction

The sequencer witness helper now accepts an optional target-stack constraint.
This matters because a shortest path to a POP address may arrive with a valid
return frame; such a path would not demonstrate underflow. A regression test
requires the empty-stack witness at 220 under the alias relaxation and checks
that it cannot be found in the unmodified scenario. Default witness behavior
is preserved.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/gate_alias_study.py
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/gate_reentry_study.py
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/program_reading.py
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -p 'test_*.py'
```

The [structural report](results/gate-alias-study/report.json) records the
identical-word classes, constrained-stack failure witnesses, superset entry
sets, four-bit search and selected scenario. The
[runtime report](results/gate-reentry-study/report.json) contains all matched
cases and two complete FC traces. No default gate or unresolved-entry label
is changed. The full plan remains incomplete.
