# Testing assumed connections from the existing photographs

The former blocker was too broad. The photos do not establish a complete
pin-level netlist, but they support a component topology from which we can build
and test explicit wiring hypotheses. Missing continuity measurements limit
verification; they do not prohibit further execution experiments.

`photo_hypotheses.py` now builds executable configurations using the actual
four PROM dumps, four LS374 models, the 8X02 sequencer and two separate Am2901
slices. No expected modem waveform is supplied by the harness. The evidence
ledger and incomplete `dsc2847.json` remain unchanged.

## What comes from where

| Connection or behavior | Basis and remaining assumption |
|---|---|
| U10→U5, U11→U6, U17→U29, U18→U30 | Visible adjacent bundles, already recorded in `nets.json`. Individual bit assignments remain untraced. Identity order is a consistent naming convention for both register inputs and outputs. |
| Two four-bit arithmetic slices | U2 and U8 are identified Am2901 devices. An eight-bit cascade, U2 as low slice, ripple carry and cross-slice shifts are assumptions. |
| U9 address→four PROMs | Assumed common ten-bit bus with no address permutation; dump structure supplies a prior. |
| Microinstruction fields | Existing q1–q4 and two fitted mappings. These are ROM-derived hypotheses, not new photo measurements. |
| Registered versus raw sequencer controls | Alternative taps before/after the LS374 bank. Arithmetic controls always come from the registers. |
| Register fetch then execute phases | Explicit assumed schedule; oscillator division and actual clock connections are unknown. |
| Condition logic | Assume direct BSR/BRT with selector zero is unconditional; other conditional transfers receive an external TEST fixture. H_* gates describe logic, not identified PCB packages. |
| Indirect branch | Compare the encoded-target stub with a mux selecting an unresolved external bus when `direct=0`. The visible U9 B3 trace toward U4 motivates investigating a separate branch path but does not establish this mux. |
| Data and initialization | External D=0 and carry=0, shift endpoints zero. RAM, Q and stack start unknown. No implicit RAM initialization, lookup-ROM path, ADC/DAC or controller protocol. |

The generated configurations include the full mapping and its SHA-256, original
PROM hashes, hypothesis explanations, and limitations. All connections are
marked hypothetical. Generic H_* logic has no claimed physical package assignment.

## Bounded experiment

The [screen](results/photo-screen/summary.json) tests six field mappings, two
sequencer-control sources, two branch treatments and three input fixtures:
**72 runs**, each bounded at 128 microinstructions. Fixed TEST=0 and TEST=1
exercise two startup paths. A third fixture pulses TEST on cycle 17, at the
baseline visit to address 008, to exercise indirect dispatch. This is a
diagnostic input pulse, not a reconstructed controller command.

The [q3 configurations, traces and final states](results/photo-hypotheses/)
preserve representative runs:

| Fixture | Result |
|---|---|
| TEST=0 | 43 distinct instruction addresses, then the 084 self-loop. |
| TEST=1 | 23 distinct addresses, then the 117–118 loop. |
| Pulse at cycle 17, encoded-target stub | 008 branches to 300; 67 distinct addresses are visited before returning to 084. Six RAM bytes become fully known in q3. |
| Same pulse, unresolved indirect bus | Stops at 008 after 17 completed instructions, because the next address depends on the unresolved bus. |

Fixed TEST fixtures do not exercise a taken indirect branch. Their completion
therefore cannot validate the encoded-target stub. The pulse makes that hidden
dependency observable. Likewise, registered and raw sequencer controls produce
the same address traces under this schedule; this test does not choose between them.

With fixed TEST, q1–q4 leave every RAM byte at least partly unknown; the two
fitted mappings make one byte fully known. This exposes an initialization/input
dependency that the earlier zero-initialized executor concealed. It does **not**
by itself reject these mappings: the D fixture, carry path, reset protocol or
instruction decode may be incomplete. The pulse run demonstrates that real
microinstructions can establish some known data without zero-filling RAM.

## Consequence for G2

The core can be run under explicit connection assumptions now. Remaining work
is to discriminate hypotheses using initialization behavior, indirect dispatch,
controller exchanges and sustained signal output. In particular, compare
candidate U4 branch-bus sources and condition/handshake logic, then constrain
the D/lookup-ROM and output paths. The 084 loop must not simply be overridden
to force a desired waveform.

These runs establish neither the correct wiring nor the modem function. G2's
controller-driven transmitter and receiver/echo-canceller checks remain unmet.
The reason to continue is that the assumptions now produce testable traces;
no additional photographs or continuity measurements are prerequisites for
trying the next candidates.

A [subsequent photo field study](../g2/PHOTO-FIELDS.md) supplies three candidate
U6→U2 B-input routes, screens the six baseline mappings against that constraint,
and executes four new A/B-swapped variants. The 72-run screen above is preserved
as the baseline experiment; it is not a ranking against those later traces.

## Reproduce

From the repository root:

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/board/photo_hypotheses.py \
  --profiles q1 q2 q3 q4 fitted_original fitted_swapped --cycles 128 \
  --summary-only --out /tmp/dsc-photo-screen
python3 nokia/data-modem-2400-2400/analysis/microcode/board/photo_hypotheses.py \
  --cycles 128 --out /tmp/dsc-photo-hypotheses
python3 nokia/data-modem-2400-2400/analysis/microcode/board/run_board.py \
  --board /tmp/dsc-photo-hypotheses/q3-registered-unknown/board.json \
  --scenario /tmp/dsc-photo-hypotheses/q3-registered-unknown/scenario-pulse17.json \
  --cycles 128 --out /tmp/dsc-photo-replay
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode/board -v
```

The last replay intentionally stops at the unresolved indirect branch. The
tests verify startup unknowns, real-ROM call/return execution, pulse-dependent
branch behavior, and replay through the standard board runner.
