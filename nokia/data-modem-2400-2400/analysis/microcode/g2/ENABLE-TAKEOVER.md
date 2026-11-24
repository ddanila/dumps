# U9 output enable and the 084 self-loop

The [previous reset-path runs](PHOTO-TABLE-CALLERS.md) end at `084`, a decoded
direct BRT back to `084`. More D bytes, TEST changes or clock pulses cannot
make that saved instruction leave the loop. The manufacturer’s
[Signetics 8X02 specification](https://bms.isjtr.ro/other/sos/Philips_elcoma_Signetics_Bipolar%26MOSMicroprocessors_1978.pdf)
(8X02 section, pages 10–11) identifies pin 2 as active-low **EN** for the
ten address *outputs*. When EN is high, those outputs are high-impedance so
another driver can address the control-store PROMs. EN does not itself load
or reset the internal address register; the document describes a separate
RESET command and clocked address register. The photographed U9 is marked
N8X02AN, so the older 8X02 document supplies a strong functional candidate,
not a pin-level measurement of this board.

[`enable_takeover_probe.py`](enable_takeover_probe.py) checks the implication
with the real four-PROM decode and the 8X02 next-address/stack model. Starting
with internal PC=`084` and an empty stack:

| Candidate bus condition | Fetched PROM word | Next internal PC |
| --- | --- | --- |
| EN low, ordinary output | `084`: BRT to `084` | `084` |
| EN high, no other address driver | Unknown | Cannot execute a known word |
| EN high, external address `036` | `036`: unconditional BRT to `300` | `300` |

The last case leaves the stack unchanged. Releasing EN would make the next
ordinary fetch use internal address `300`, whose real PROM word is INC.
The diagnostic is a **control-store bus takeover**, not an injected PC:
the 8X02 executes the BRT actually fetched from PROM address `036` and loads
its encoded branch target on the next clock. The script finds 76 direct,
unconditional BRT words other than the `084` self-branch that could serve as
one-cycle vector words under the saved decode. `036` is one illustrative
choice, not a recovered Nokia vector.

The board evidence does not yet connect U9 EN to a controller signal or show
a second ten-bit address driver. U4 is a photographed 74LS244 eight-bit
buffer, and the one [visible track fragment](../board/nets.json) runs from
U9 B3 toward U4; it does not establish that U4 drives the PROM address bus.
Thus this experiment identifies a datasheet-permitted hypothesis to test,
but no actual restart, controller-driven transmitter or receiver. A next
photo-informed board configuration must specify both the EN timing and all
ten externally driven address bits, and keep the internal stack state when
replaying real controller events.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/enable_takeover_probe.py
```

The [saved report](results/enable-takeover-probe.json) records the fetched raw
PROM words, next addresses, stack check, vector list and source hashes.

## Four-PROM board replay

The [board-level follow-up](board_enable_takeover.py) builds on the existing
board model with the original q3 field mapping. It does not yet include the
later photo-constrained Am2901 pin assignments. It adds **two hypothetical
eight-bit buffer primitives** to supply a ten-bit address; they are a
diagnostic adapter, not
an attribution to U4. U9 EN and the adapter drive have separate controls.
The event first disables U9's address outputs, then enables the external
driver, avoiding a period with two active address drivers. After one normal
register-fetch and sequencer/ALU clock cycle, it disables the external driver
and re-enables U9. The four real PROMs and four LS374 control registers
participate; RAM/Q retain the board model's unknown power-on state.

In a matched 128-cycle TEST=0 run, the baseline first reaches internal `084`
at cycle 42 and stays there. The candidate handoff at that same cycle makes
the PROM bus float for one event, then reads address `036` as raw bytes
`01 DC 83 FC`. U5/U6/U29/U30 latch those exact bytes; U9 clocks to internal
`300` with its stack unchanged. After release, the ordinary PROM address is
`300`. The candidate spends 43 cycles at addresses in the `300`–`3FF`
region, but returns to `084` before cycle 128. It makes no call at `3C2` or
`3D7`. The takeover is executable in the full board timing model. This
particular vector and TEST fixture do not establish recurring signal
processing.

The [board report](results/board-enable-takeover.json) retains the event
witness, matched coverage counts, PROM hashes and exact candidate wiring
description. The external address and EN signals remain **untraced**; no
controller, ADC or DAC is connected in this replay.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/board_enable_takeover.py
```
