# DSC2847 photo-only board reconstruction

**The software infrastructure is implemented; the Nokia circuit reconstruction
remains incomplete. No faithful Nokia microcode execution has been achieved.**
The real-board configuration preserves unresolved connections instead of using
the earlier illustrative instruction map. Its startup run stops before the
first cycle because the clock relationships have not been recovered.

The integration demonstration executes synthetic microcode through a PROM,
edge-triggered control register, 8X02 and two separate Am2901 models. Its eight
cycles exercise call, return, increment and reset. This tests the simulator;
it does not establish Nokia's instruction format or validate the dumps.

## Evidence and reconstruction result

- [Front annotated view](evidence/front-annotated.jpg) and
  [mirrored-back annotated view](evidence/back-annotated.jpg) share an approximate
  board coordinate frame. Rectified unannotated views are alongside them.
  These are tracing aids, not precise layer overlays. Original photos remain
  untouched; transformations and hashes are in [the manifest](evidence/manifest.json).
- [Inventory](inventory.json) accounts for all 30 numbered positions, including
  unpopulated U16. U20 and U23 remain unreadable; U22 has only a tentative
  identification. U12 reads LS175, U14 LS75, U24 LS161 and U25 LS74.
- [Connection evidence](nets.json) records four inferred PROM/register bundle
  pairings and one visible trace fragment from U9 pin 17 (B3) toward U4. That
  fragment disappears beneath the buffer package; its other endpoint remains
  unknown. **There are zero complete executable pin-to-pin nets in this
  reconstruction.** Bundle adjacency has not been promoted to bit assignments.
- [Board configuration](dsc2847.json) instantiates the eleven identified core
  devices with unknown inputs. The remaining populated positions are listed
  explicitly as unmodeled, not replaced by invented behavior. Physical pin
  tables are available for the PROMs, control registers and sequencer.
- [Specifications](sources.json) identify the primary references consulted,
  including hashes of locally inspected historical PDFs where available.

The supplied photographs permit useful component identification and visible
trace segments, but this attempt did not recover a complete control path.
Paths beneath packages and uncertain via continuations prevent assigning the
sequencer command/condition, ROM address permutations, clock phases, and slice
controls with confidence. No complete candidate netlist is sufficiently
constrained to enumerate meaningful alternatives. The earlier arbitrary map
remains separately preserved in the parent directory and is not imported here.

## Run and inspect

From the repository root, Python 3 with its standard library:

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/board/run_board.py \
  --board nokia/data-modem-2400-2400/analysis/microcode/board/dsc2847.json \
  --scenario nokia/data-modem-2400-2400/analysis/microcode/board/startup.json \
  --cycles 1000 --out /tmp/nokia-board-startup

python3 nokia/data-modem-2400-2400/analysis/microcode/board/run_board.py \
  --board nokia/data-modem-2400-2400/analysis/microcode/board/synthetic-demo.json \
  --scenario nokia/data-modem-2400-2400/analysis/microcode/board/synthetic-scenario.json \
  --cycles 8 --out /tmp/nokia-board-synthetic

python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode/board -v
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -v
python3 nokia/data-modem-2400-2400/analysis/microcode/board/validate_evidence.py
```

The first command completes normally with a **blocked reconstruction result**,
not a successful boot. Read `summary.json`: cycle-limit completion and a
modeled stop are distinct. Invalid configuration or corrupt ROM input exits
with an error. All original ROM sizes and SHA-256 hashes are checked explicitly,
including under `python3 -O`. No programmer or physical hardware is accessed.

Checked-in results are under [results/startup](results/startup/) and
[results/synthetic](results/synthetic/). Each contains:

- Validation report and a summary of execution status and limitations.
- `trace.jsonl`: event/phase, external inputs, internal signals, register state,
  both slice RAM/Q arrays, sequencer stack, pending next address and stop state.
- `raw-prom-lanes.csv`: original bytes indexed by physical file offset.
- `rom-listing.csv`: static sequencer-address inspection, physical lane
  addresses, data and decoded fields where known; `?`/`X` marks unknowns.
- `control-flow.json` and Graphviz `control-flow.dot`: conditional and dynamic
  targets. The Nokia graph has an unresolved edge from startup, not a guessed
  disassembly. Static decode does not initialize or bypass physical registers.

## Configuration and model boundaries

A component has a type and named input ports; the inventory separately records
physical pins where established. Inputs can be unsigned integer constants,
`null` for unknown, an output reference such as `U9.A`, a bit reference such as
`U9.A[3]`, an LSB-first bit list, `{"not": expression}`, or
`{"bus": [driver, ...]}`. External inputs use `EXT.name` and explicit widths.
Missing inputs remain unknown. Type/port/width validation and bus contention
checks reject invalid connections. Only synthetic-test boards may embed ROM
bytes; other ROMs require a file and expected hash.

Scenarios provide initial external input levels and an ordered, repeating list
of named input-change events. There is no default oscillator, reset pulse,
clock order, connector pin assignment, or wall-clock frequency. Data should be
established in a separate event before its sampling edge; this is not an
analog setup/hold simulator. Static `decode` fields are optional explicit
expressions for fetched control signals and must carry the board's evidence
status; they do not alter the runtime circuit.

Implemented primitives include PROMs, LS374 registers, LS373 transparent
latches, separate four-bit Am2901 slices, an 8X02 adapter, logic gates,
multiplexers, tri-state buffers, and an abstract loadable four-bit counter.
The generic counter/buffer/multiplexer are building blocks, not drop-in models
of every numbered TTL package. Unmodeled board parts must be reconstructed
and adapted before claiming complete operation.

Unknown and high-impedance values are explicit, distinct four-state bits.
Unknown data propagates through arithmetic and storage; it is never silently
zeroed. The runner stops when unknowns determine a sequencer transfer, a RAM
write address, active instruction control, a clock transition, or an explicitly
designated observable. Unknown data may remain in unused registers. A trace at
a stop can represent a partially processed event, which is labeled accordingly.

The engine settles combinational logic, samples devices together at an edge,
and settles transparent storage afterward. Am2901 A/B input latches follow RAM
while its clock is high, RAM writes occur in the low phase, and Q updates on a
rising edge. The 8X02 adapter performs stack operations in the falling phase
and transfers the prepared next address on the rising phase. It **requires
relevant controls to remain stable between those phases**; changes are rejected
rather than treated as known hardware behavior. A rising edge without a
prepared falling phase is also rejected. Sequentially generated clocks require
an additional timing adapter and are explicitly rejected in this version.

Remaining chip-model limitations include Am2901 logic-operation carry/overflow
and active-low carry-lookahead outputs, which are not yet implemented. Logic
carry/overflow read as unknown. Power-on RAM/Q and stack contents are unknown;
the 8X02 address starts at its documented power-on zero. No propagation delays,
analog path, external memory protocol, or other modem boards are simulated.

## Verification and next evidence needed

**18 new tests plus the original 11 pass.** They cover unknown/tri-state logic,
exhaustive nibble arithmetic flags, ROM integrity and permutations, transparent
versus edge-triggered storage, simultaneous sampling, conditional sequencing,
call/return, invalid timing, separate-slice carry and RAM/Q shifts, deterministic
replay, static decode, and synthetic control-store integration. Evidence audits
check identifiers and pin ranges, not continuity.

The next meaningful reconstruction requires resolving the six groups listed
in `dsc2847.json`: CLOCK, ADDRESS, REGISTER, SEQUENCE, DATAPATH, and EXTERNAL.
Particularly useful endpoints remain U9 AC0/AC1/AC2 (pins 27/28/1), TEST (26),
clock (25), and the clock/enable inputs of the four control registers. Further
photo tracing can extend the evidence ledger; if supplied images cannot resolve
these paths, additional evidence would be necessary. This implementation does
not ask for measurements or assume them available under the photos-only scope.

To regenerate documentary views, install Pillow in a separate environment and
run `prepare_photos.py`. It reads original images and inventory coordinates;
it writes only derived evidence images and their manifest. No graphics package
is needed to execute or test the models.
