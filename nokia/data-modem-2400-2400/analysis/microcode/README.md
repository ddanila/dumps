# DSC2847 bit-slice execution experiment

**Current experiment:** [the assumption-driven workflow](assumed/README.md)
implements the analysis and execution tooling from [PLAN.md](PLAN.md). A new
[local branch-table hypothesis](assumed/BRANCH-TABLES.md) raises measured
sequencer coverage from 28.8% to **55.3%**, with clean million-cycle runs and
three speculative datapath variants. The 90% coverage target and identification
of the actual datapath/I/O remain unmet. Historical results are preserved in
[the baseline report](assumed/RESULTS.md). A subsequent
[register-field study](assumed/REGISTER-FIELDS.md) identifies a second counting
field and shows that the current datapath candidates still fail to explain
chip-10 differences between dispatch entries. The newer
[paired-arithmetic experiment](assumed/PAIRED-ARITHMETIC.md) tests chip-10
function/carry controls, yielding conditional rotation and add/subtract
interpretations, with an explicit overlapping-register counterexample.
A [caller-state study](assumed/CALLER-STATES.md) additionally finds nonzero-Q
counterexamples on reset paths when the external input stub is nonzero.
The [separated source-bit search](assumed/Q-INDEPENDENT.md) removes that Q
dependency and supports a conditional shift-until-zero interpretation of 1E9.

A subsequent [photo-only board reconstruction](board/README.md) adds a
four-state event model, separate slices, explicit storage/clock behavior,
annotated evidence, static listings and a tested synthetic integration path.
The real Nokia wiring remains unresolved; its strict startup scenario executes
zero cycles. The illustrative experiment below is preserved as historical
evidence and is not used as the new board configuration.

The board contains a **Signetics N8X02AN control-store sequencer** at position 9,
confirmed by the [close-up](../../photos/PXL_20261123_113232157.jpg) and
[whole-board photograph](../../photos/PXL_20261123_114926601.jpg). It accompanies
both Am2901BDC slices and the four 1024-byte PROMs. The 8X02 has a 10-bit program
address and a four-entry return/loop stack. This makes the proposed 1024-word
microprogram architecture substantially more concrete.

**We have not yet recovered Nokia's microinstruction format or demonstrated
faithful execution of its microcode.** A functional datapath/sequencer model
and a configurable real-ROM runner now exist. The first illustrative mapping
reaches an uninitialized stack read at address 001 after two microinstructions.
The result exposes an unsupported mapping/startup assumption; it says nothing
about the integrity of the PROMs.

## What actually ran

`run.py` verifies all four original PROM hashes and reads the original bytes.
The supplied `illustrative-map.json` deliberately carries an UNVERIFIED label:
its assignments are a software experiment, **not a photo-traced wiring map**.
It uses chip 10's low three bits as the sequencer command, chip 11's low six
bits plus chip 17's high three bits as the Am2901 instruction, and chip 18 as
register addresses/data/part of a branch address. Sharing these fields, their
polarity, and their significance are all unproven. Bits not used by this map
are ignored; external controls they might represent are not modeled.

All three runs (TEST held low, held high, or driven by the modeled ALU zero
result) stop at the same point. Chip 10 begins `01 03`, interpreted by this
mapping as INC followed by POP, without a preceding push. The model refuses to
invent an initial return address. This rejects this combination of mapping and
startup assumptions as a self-contained explanation of startup; it does not
exclude externally initialized stacks, address permutations or latch timing.

A guessed map can easily produce loops without explaining the hardware. The
runner therefore requires an explicit mapping argument, reports its status,
and records raw PROM bytes alongside decoded fields. No trial trace is called
a successful modem boot. Results are in [results/summary.json](results/summary.json).

## Reproduce

From the repository root, using Python 3 (standard library only):

```sh
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -v
python3 nokia/data-modem-2400-2400/analysis/microcode/run.py \
  --mapping nokia/data-modem-2400-2400/analysis/microcode/illustrative-map.json \
  --out /tmp/nokia-microcode-results
```

A map field is an integer constant or an LSB-first list such as
`["10.0", "10.1", "!17.3"]`; `!` inverts a bit. Chip numbers are physical board
positions, not byte significance. Address wiring is currently assumed straight
through: sequencer address N reads offset N in all four files.

## Implemented and tested behavior

`model.py` implements the Am2901's eight operand pairs, eight ALU operations,
eight destination modes, sixteen registers and Q register. Width 8 represents
two ordinarily cascaded slices; width 4 is available for individual slices.
Arithmetic carry and overflow, ALU zero/sign, A-output selection, and explicit
external shift input bits are modeled. Logical-operation carry/overflow pins
return `None`, because their hardware equations are not yet implemented.

The 8X02 implements all eight commands, modulo-1024 address arithmetic, its
four-entry circular stack, and conditional calls/branches. BLT decrements the
stack pointer even with TEST low; RST changes the address without clearing the
stack. Power-on stack contents remain unknown. Stack index origin is arbitrary
and does not imply a documented physical power-on pointer value.

All **11 tests pass**, including exhaustive 8-bit add and both subtraction
operations for both carry inputs, signed-add overflow, each operand/destination
selection, logic results, inter-slice carry, nested calls, skip/wrap, and the
BLT/RST details. These validate modeled components, not Nokia's wiring.

This is a functional step model, not a circuit or clock-phase simulation.
PROM output latches, clock gating, tri-state buses, internal carry-lookahead
pins, external RAM/I/O, inter-board traffic and analog circuitry are absent.
RAM/Q start at zero for reproducibility, not because the physical Am2901
promises that power-on state. Carry and shift inputs are zero in the example.
The board's condition logic may use registered flags or other signals rather
than the current ALU zero result. None of these choices has been measured.

## Connections needed for a meaningful next run

Use the front/back photographs as a tracing aid, then confirm ambiguous nets
with unpowered continuity checks. Start at the sequencer: only three command
signals determine whether the first two PROM rows really mean INC/POP.

| Position 9, 8X02 pin | Signal | Required evidence |
| --- | --- | --- |
| 27, 28, 1 | AC0, AC1, AC2 | Trace each to its latch output or intervening logic, then to the PROM output bit; record inversions |
| 26 | TEST | Identify condition-selection gates, source flags and polarity |
| 14, 15, 16, 17, 18, 19, 20, 21, 23, 24 | B0 through B9 | Identify branch-address sources, including any muxes |
| 3, 4, 5, 6, 8, 9, 10, 11, 12, 13 | A0 through A9 | Confirm corresponding address pins on all four PROMs |
| 25, 2 | CLK, active-low output enable | Establish sequencing/latch phase and external address ownership |

The four nearby SN74LS374 latches are at positions 5, 6, 29 and 30. Establish
which PROM data output feeds which latch input, then trace latch outputs to
Am2901 I0–I8, A0–A3, B0–B3, carry, data, and shift connections. Do not assume
adjacent chip numbering implies matching bit order. The board photos include
traces obscured by packages, solder/glare, and side transitions; no complete
netlist was obtained in this attempt.

Once these connections are known, replace the illustrative map and implement
any intervening mux/condition/clock logic before treating a trace as evidence
of the original algorithm. The other boards will still need models to run a
complete modem signal path.

## Primary specifications consulted

- Signetics, *Bipolar/MOS Microprocessor Data Manual* (1978), printed pages
  10–12 (PDF pages 12–14), 8X02 pin configuration and command tables:
  [manufacturer databook scan](https://bms.isjtr.ro/other/sos/Philips_elcoma_Signetics_Bipolar%26MOSMicroprocessors_1978.pdf).
  The pin drawing explicitly identifies AC2=1, AC1=28, AC0=27; the compact
  pin-designation table's ordering should not be substituted for that drawing.
- AMD, *Am2901B/Am2901C Four-Bit Bipolar Microprocessor Slice*, document
  01656B, printed pages 5-5 and 5-6 (PDF pages 5 and 6):
  [manufacturer datasheet scan](https://pccomponents.com/datasheets/ADVAN-AM2901BDMB.pdf).

Raw dumps and photographs were not modified, and no programmer operations were
performed for this experiment.
