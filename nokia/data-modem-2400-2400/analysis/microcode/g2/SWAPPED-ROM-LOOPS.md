# ROM-fed loops under photo-compatible A/B swaps

**Mapping update:** The later [I7 photo constraint](PHOTO-FIELDS.md#i7-instruction-input-is-a-new-conditional-constraint)
challenges the PROM-bit I7 assignment retained in these A/B swaps. In the
q3 fixture, both fixed levels of the candidate E4-side I7 signal leave the
output loop. The runs below describe the declared mappings and remain useful
counterfactuals; their loop interpretation is not established board behavior.

The three candidate U6→U2 B-input traces in [PHOTO-FIELDS](PHOTO-FIELDS.md)
allow A/B-swapped variants of the q1–q4 instruction mappings. These runs test
two reopened paths with the real control PROMs and Am27S31 bytes. The swaps,
ROM-enable gates and external input schedules remain explicit hypotheses.

## q3: sine byte reaches paired output, but does not advance

[`swapped_sine_loop.py`](swapped_sine_loop.py) runs the q3 swap for each of the
65 quarter-sine phase inputs (0–64), for 1,024 microinstructions each. The
global two-bit diagnostic ROM gate selects real ROM bytes on D at 115 and 317.
At phase 32 the read at 317 uses ROM address 120 and returns byte 90. The
candidate output words 392–395 then repeat every 12 instructions, 81 complete
groups in this run, always **0, 0, 190, 64**. Phase 64 repeats **0, 0, 8,
129**. Phase zero produces one group **0, 0, 10, 0** before reaching 084.

With the same phase-32 fixture and all other selected ROM reads intact,
replacing only the D input at 317 with zero changes the quartet to **0, 0,
10, 64**; it still repeats 81 times. This counterfactual directly establishes
that the real ROM byte affects the candidate output under this mapping.

All 64 phases with repeated groups have **one distinct group per run**. Thus
this fixture shows ROM-dependent output but no changing output within a run.
Different groups across reset runs
come from the phase externally supplied at 316. The 392–395 ALU Y bytes are
candidate outputs; their connection to the DAC has not been traced. The
[report and phase-32 witness](results/swapped-sine-loop/report.json) include
the exact mapping, scenario, trace, ROM hashes and source hashes.

## q2: a second ROM-fed loop settles to a fixed point

[`swapped_q2_rom_loop.py`](swapped_q2_rom_loop.py) tests all 16 diagnostic
gates that select a D operand at 127, using the same phase-32 input fixture.
Eight gates revisit 127 **118 times** in 512 instructions, with actual ROM
data selected on D on every visit. In the smallest-gate witness, the first
read is address 100 → 0, then address 101 → 3 repeats; ALU Y at 127 stays 3
after that first transition and Q stays zero. Two other repeating gates settle
at ROM address 10B → 34. The other eight gates reach 127 only once and take
different routes in this fixture. Every repeating case has a
constant ALU Y value for its last 16 visits. The [report and witness](results/swapped-q2-rom-loop/report.json)
preserve each gate, selected read, state value and trace.

Four of the eight gates that leave 127 enter a second ROM-fed loop at **12C**.
They select real ROM data on all 116 visits in the 512-instruction fixture.
The first read is at 1FF → 0B, then 101 → 03 repeats; Q stays zero and Y at
12C stays 3 for the last 16 visits. The updated report records these four
cases and includes a separate 12C trace witness. Thus the additional q2 site
also settles in this input fixture.

These are useful negative tests for the present candidate wiring and stimuli:
neither loop demonstrates an evolving transmitter waveform or C2. A changed
ROM gate, input schedule, sequencer decode, or another routine can still
produce one. The next experiment should supply a controller-derived sequence
of dibits and examine whether a decoded phase state changes across symbol
boundaries, while keeping photo-based connection alternatives explicit.

## New photo-constrained q1 loop: an exact 20-value ROM recurrence

The [later photo constraints](PHOTO-FIELDS.md#photo-constrained-startup-and-controller-bit-run)
put U2 A2/A3 tentatively on U10 D7/D6 and U2 I7/I0/A0/A1 on two possible
enable-side signals. Applying those choices to the q1 and q2 photo-swapped
variants changes the behavior of the 127/12C loops. The
[reproducible gate sweep](photo_variant_rom_loop.py) executes the real PROMs
for 2,048 microinstructions under every one of the **16 diagnostic gates**
that select Am27S31 data at 127, starting with Q and RAM zero.

In **q1**, every gate visits 127 once, then reads the Am27S31 at 12C **500
times**. After the first read at `1FF→0B`, each address is exactly
`0x100 + ((previous ALU Y + 1) mod 256)`. The run has eight transient reads,
then repeats the same **20-value** ALU Y cycle under all 16 gates:

`23, 71, 29, 85, 19, 60, 127, 9, 31, 90, 17, 54, 124, 7, 25, 76, 24, 73, 26, 78`.

The [witness trace and report](results/photo-variant-rom-loop/report.json)
preserve the mapping, scenario, gate, every address and the full execution.
This is the first sustained, changing ROM-fed loop under the photo-level
assumptions. Its values are produced by iterating a lookup-table function;
the ROM address does not advance by a constant phase step, and no physical
DAC output, sample rate or controller-driven symbol change is established.
Therefore the 20-cycle repetition is **not** a demonstrated line carrier.

In **q2**, eight gates remain in the 127 loop, where ALU Y settles to 3 or
34. The other eight enter 12C: five settle to 3 and three alternate 49/40.
Those small fixed points and two-cycles also fail to show a phase-advanced
sine carrier. All of these conclusions are conditional on the photo routes,
ROM-enable fits and q3-derived diagnostic scenario.

## Fitted mapping: changing ROM addresses lead through a finite drain

The photo-compatible `fitted_swapped` mapping has another reopened ROM-fed
site at 299. [`fitted_rom_drain.py`](fitted_rom_drain.py) runs all **48**
diagnostic gate fits that select that site. Its reset fixture uses dispatch
index 1 and the existing D=FF early-reply schedule; these are diagnostic
inputs, not decoded controller commands. All 48 runs read the real ROM at 299,
with two to five visits each, and none visits candidate output word 392 in
2,048 instructions. In the smallest-gate witness, successive reads use
addresses **1FE, 17F, 13F** and return **0A, 08, 7F**. Q at those reads is
**FE, 7F, 3F**. The trace shows Q shifting at 29D between visits; changing
ROM addresses here are therefore a finite drain path, not evidence of a
running carrier phase. Some gates also select ROM at other words and take
different routes, but all 48 miss the candidate output in this fixture.
The [saved sweep and witness](results/fitted-rom-drain/report.json) preserve
each gate, read sequence, full trace digest and input assumptions.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/swapped_sine_loop.py
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/swapped_q2_rom_loop.py
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/photo_variant_rom_loop.py
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/fitted_rom_drain.py
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode/g2 -p 'test_swapped_rom_loops.py' -v
```
