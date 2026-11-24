# DSC 2847 bit-slice microcode

The DSC 2847 board is a microprogrammed 8-bit datapath: two Am2901BDC slices
driven by a Signetics N8X02AN control-store sequencer. Its control store is
four MMI 6381 PROMs ([810237C–810240C](../../microcode-810237c-810240c/)),
which most likely form 1024 words of 32 bits each. The board very probably
does the modem's sample-rate signal processing, but its wiring has not been
traced, so the microcode runs only under explicit, labelled assumptions.

## Status

- **Done, goal G1 ([PLAN.md](PLAN.md)):** the microcode runs without model errors
  under six candidate field mappings. Every used word is annotated, and a
  controller-to-DAC transaction is replayed. See the
  [overview](assumed/PROGRAM-OVERVIEW.md) and the
  [final review](assumed/FINAL-REVIEW.md).
- **Not yet known:** the algorithm itself. Under the current mappings the
  microcode produces constant DAC codes, not a waveform.
- **Next, goal G2 ([PLAN-2.md](PLAN-2.md#goal-g2)):** use the V.26 ter evidence from the
  controller (scrambler, synchronous line USART, handshake timing, 14.4 MHz
  clock, sine tables) to rule mappings in or out by what a DPSK modem must
  compute. A few continuity checks on the board would settle the rest.

## What is here

| Path | Contents |
| --- | --- |
| [assumed/](assumed/) | The main experiment: field analysis, sequencer and datapath execution, about 115 studies indexed by topic, and [ASSUMPTIONS.md](assumed/ASSUMPTIONS.md) |
| [board/](board/) | Photo-only board reconstruction: 30-position inventory, annotated views and a four-state event model. No complete nets are recovered, so its strict real-board startup executes no cycles. |
| `model.py` | Functional Am2901 (two cascaded slices) and 8X02 models, used by everything above |
| [history/](history/) | The first [illustrative run](history/ILLUSTRATIVE-RUN.md) with a guessed mapping (`run.py`, `illustrative-map.json`) |

## Component models

`model.py` implements:

- **Am2901:** all eight operand pairs, ALU operations and destinations, the
  16 registers and Q, carry/overflow/zero/sign, and external shift inputs.
  Logical-operation flags follow the datasheet's Figure 9 when enabled.
- **8X02:** all eight commands, modulo-1024 addressing, the four-entry
  circular stack, and conditional calls and branches.

It is a functional step model, not a clock-phase simulation. The component
tests check arithmetic exhaustively for 8 bits, plus stack, skip and wrap
behaviour. They validate the models, not Nokia's wiring.

## Reproduce

From the repository root, with Python 3 (standard library only):

```sh
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -v
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode/board -v
(cd nokia/data-modem-2400-2400/analysis/microcode/assumed && python3 plan_validation.py)
```

Study-specific commands are in [ASSUMPTIONS.md](assumed/ASSUMPTIONS.md) and
in each study.

## Primary specifications

- Signetics, *Bipolar/MOS Microprocessor Data Manual* (1978), pages 10–12:
  8X02 pinout and command tables
  ([databook scan](https://bms.isjtr.ro/other/sos/Philips_elcoma_Signetics_Bipolar%26MOSMicroprocessors_1978.pdf)).
  Use the pin drawing (AC2 = 1, AC1 = 28, AC0 = 27), not the compact table.
- AMD, *Am2901B/Am2901C Four-Bit Bipolar Microprocessor Slice*, document
  01656B, pages 5-5 and 5-6
  ([datasheet scan](https://pccomponents.com/datasheets/ADVAN-AM2901BDMB.pdf)).
