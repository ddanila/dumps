# Third outgoing byte combines counter state and code flags

Controller section 012F–0263 builds RAM 32, the third outgoing byte, and updates
RAM 49, 4A, and 65. The serial routine sends RAM 32 without an XOR mask. This
completes local reference descriptions of all four output-byte builders, but
not their full polling-loop integration or physical interpretation.

The reference is `output32` in [controller_output.py](../../controller_output.py).
It uses state S=RAM 34, decoded flags at 22–24, received C=RAM 2C, and raw state
code K from the [preceding lookup](CONTROLLER-OUTPUT.md). Local entry supplies
R3=S and R2=K, as established by that preceding section.

## Output fields

| RAM 32 bit | Behavior |
| --- | --- |
| 7 | Selected by state class; enabled in the counter-processing paths |
| 6 | Retained or toggled by the counter rules below |
| 5 | Counter phase flag: set on certain resets/reloads, cleared on the following phases; retained in the disabled state class |
| 4 | Clear when flag 24.5 or 23.5 is set; otherwise one for RAM 65 in 14–93 inclusive, zero outside that range |
| 3 | Copy raw code K bit 0 |
| 2 | One only when S=00 and flag 24.5 is set |
| 1:0 | Selected from raw K bit 2, flags 23.5/22.3, and S; rules below |

All numeric ranges here are hexadecimal unless stated otherwise. Flag 24.5
also resets RAM 65 to zero. The bit-4 interval follows the actual wrapping
8-bit addition and sign test; replacing it with an unbounded threshold would
produce different results for large byte values.

For bits 1:0: when K bit 2 is set, the pair is 10 if 23.5 or 22.3 is set,
otherwise 01. When K bit 2 is clear, the pair is 10 for S=00/01 and 00 for
other states. The low bits of the state-code table therefore carry information
used outside the fourth output byte.

## Counter paths

States C2, C3, and E4 take the special counter path. It sets bit 7. If flag
24.5 or received C0 is set, it clears counters 49/4A and sets bit 5. Otherwise
it clears bit 5 and updates the two counters using wrapping additions,
subtraction-with-borrow, and sign tests. Some results toggle bit 6 and increment
4A. The reference preserves these exact byte operations and carry dependencies;
it does not assume that 49/4A form a conventional 16-bit timer.

Outside that class, states with S bit 6 set, or S=96/B6/B7, clear bit 7 while
leaving the high counter-related fields and counters otherwise intact before
the common low-bit assignments.

The remaining states set bit 7 and use this sequence:

1. Flag 24.5 sets bit 5 and reloads counter 49 with ten (decimal).
2. With bit 5 set, calls decrement a nonzero counter 49. Once it is already
   zero, the builder clears bit 5 and reloads 49 from the ROM table at
   `01BE + (S AND 3F)`, rotated left twice. S bit 7 clear instead reloads zero.
3. With bit 5 clear, a nonzero counter 49 is decremented. Bit 6 toggles whenever
   its new low two bits are both one. At zero, the counter and bit 6 hold.

The ROM table contains values 0–0E, so those reloads are multiples of four.
If other code leaves the counter alone and flags stay fixed, this produces a
finite sequence of toggles, not a perpetual oscillator. These are counts of
builder calls, not a recovered physical period.

RAM 49 also has writers at 188E and 189F–18A3, following an XOR comparison and
bit-counting loop elsewhere in the controller. RAM 65 is likewise changed by
another routine. Consequently, the local counter behavior must not be treated
as independent of the rest of the firmware. Those caller/data relationships
need further interpretation before assigning a physical status meaning.

## Verification

[Configuration](../../controller-output32-scenario.json) declares local entry
012F, stop 0266, bank zero, disabled interrupts, and supplied register/code
values. The 103,424 cases include:

- 128 seeded combinations of flags, prior output, received C, and all three
  counters for each of the 256 state bytes.
- All 65,536 combinations of counters 49/4A in state C2's special path, with
  initial bit 6 varied across the sweep.
- Every RAM 65 byte under relevant flag combinations and representative states.
- Every prior output byte at eight representative states.

Every case matches all 128 internal-RAM bytes, stop PC, and unchanged stack
pointer, without emulator exceptions. All 112 instruction starts in the section
are visited; the 64-byte ROM table at 01BE–01FD is excluded as data. The sweep
is exhaustive over the stated subproblems, not the entire joint state space.

```sh
python3 nokia/data-modem-2400-2400/analysis/controller_output32_study.py
```

[Report](../../results/controller-output32-study/report.json) includes source
and ROM hashes, execution/fixture digests, coverage, and 32 complete witnesses.
The [continuous construction study](CONTROLLER-OUTPUT-BUILD.md) now checks all
four builders together and the immediate RAM30/P1 override. The rest of the
006E routine and its composition with serial transfer remain to be verified.
