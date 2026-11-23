# Received controller bytes feed a stateful bit-field decoder

The 8031 main loop calls input routine 0800 at 1ED6, then calls 0620 at 1ED9.
The latter interprets normalized input bytes at RAM 2A–2F as selectors and flags,
updates state at 22–24, and can rewrite the received bytes themselves. A
[reference implementation](../../controller_decode.py) now reproduces this
routine's internal-RAM effects against the unchanged ROM.

This is controller-side program reading. Physical switch/status names and the
connection to the DSC2847 remain unidentified. These bytes are not established
as six numerical DSP samples.

## Input convention and override

Use A–F for the six normalized bytes at 2A–2F. A is the first payload byte XOR
07; B–F are unchanged by the [serial receive routine](CONTROLLER-INTERFACE.md).
The discarded preliminary transfer is not part of A–F.

At 0622–063E, the predicate

```
C7 AND C6 AND D0 AND B1 AND B0 AND B3 AND B2
```

causes these input edits: clear F6, set F5, set D7, clear D0, clear B1, and clear
E7 and E6. Subsequent decoding uses the edited bytes. RAM 22.2 is then set
unconditionally at 0640, whether or not that override occurred.

## Derived mode and change detection

Bits F6/F5 select the new RAM 22.3 value:

| F6 | F5 | New 22.3 |
| --- | --- | --- |
| 0 | 0 | C7 |
| 0 | 1 | 0 |
| 1 | 0 | 1 |
| 1 | 1 | B4 |

The old 22.3 is copied to scratch bit 20.0. RAM 22.1 becomes old XOR new,
indicating a change in this derived mode. RAM 22.0, the earlier receive-frame
change flag, is preserved; the two flags report different changes.

## Selector priority and other output flags

At 066B–06B5, the routine clears RAM 23.4–23.7 and 24.6, then uses the first
matching row below. Competing asserted inputs therefore do not accumulate:

| First satisfied condition | Set bits | Additional assignment |
| --- | --- | --- |
| C3 | 23.4, 23.5 | 24.6 = C4 |
| C1 | 23.4, 23.7 | — |
| C2 | 23.4, 23.6 | 24.6 = C4 |
| C4 | 23.4, 24.6 | — |
| B2 AND B1 | 23.4, 23.5 | — |
| B3 AND D0 | 23.4, 23.6 | — |
| None | None | — |

The next section combines this selection, the derived mode, A/B/C/F bits,
previous RAM 22.5, and a comparison of RAM 6E with FF. It selects one of four
updates to RAM 22.4/22.5: set bit 4 and preserve bit 5; set both; set bit 4 and
clear bit 5; or clear both. Some paths also set received bit F2. The reference
keeps those actions distinct, especially the state-preserving case. The purpose
of RAM 6E is not established by this local study.

Finally, 072F–077B derives RAM 23.1–23.3 from E selector bits and A5/B4/B5/C5.
RAM 22.5 forces 23.1 high. E3 forces both 23.2 and 23.3 high; otherwise those
two outputs are complementary. All unrelated internal-RAM values are preserved
apart from scratch bit 20.0 and the explicitly described writes.

## ROM execution checks

[Configuration](../../controller-decode-scenario.json) supplies normalized input,
previous RAM 22–27, and byte 6E. Each local execution begins at 0620 with a real
return frame and interrupts disabled. It checks return PC, stack pointer, no
emulator exceptions, and all 128 internal-RAM bytes against the reference.

The 10,144 cases comprise:

- 1,536 one-byte sweeps: all 256 values at each of the six input positions.
- 128 assignments of the seven-bit override predicate.
- 32 assignments of mode-selector/source bits and prior mode state.
- 256 assignments of the priority-selector inputs, including overlaps.
- 8,192 seeded cases varying all six received bytes, all six prior state bytes,
  and byte 6E, including FF and nearby values.

The cases execute all 153 instruction starts in 0620–077B; the study
checks this against the saved disassembly. Instruction coverage does not imply
exhaustive state coverage. This is exhaustive over the listed subproblems, not all combinations of the
48 input bits and prior state. Thirty-one representative override/priority/action
combinations have complete saved states. The mode and priority truth tables are
based on instruction reading and checked by execution; physical labels are not
inferred from the tables.

```sh
python3 nokia/data-modem-2400-2400/analysis/controller_decode_study.py
```

[Report](../../results/controller-decode-study/report.json) includes assumptions,
source and ROM hashes, fixture/execution digests, and witnesses. The shared C
probe adds an explicit `decode` mode without changing earlier mode behavior:
all 4,362 interface fixtures and 2,048 external-read probes retain identical
execution digests and witnesses. The reference does not replace ROM execution
in the controller harness or create a speculative DSP bridge.
