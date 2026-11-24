# Explicit DAC0830 output hypotheses

*Runs under the [shared assumptions](ASSUMPTIONS.md).*

A new opt-in digital DAC sink makes candidate output connections testable
without identifying any of them as recovered wiring. It consumes completed
microcode traces, so the CPU, reads, dispatches and earlier virtual output
records are unchanged. It does not generate a continuous waveform or assign
an analog voltage or physical sample rate.

## Evidence and component boundary

**Hardware correction:** The [DED3558 photograph](../../../photos/PXL_20261123_114854803.jpg)
shows a stickered **ADC0800PCD**, an A/D converter, not a confirmed DAC0830.
See the [photo and datasheet review](../g2/ADC0800-INPUT.md). No DAC0830 has
been identified on DED 3558 from this photograph. The model below is an
explicit *counterfactual output adapter*; it does not establish a route from
the DSC2847 ALU bus, an intervening latch, byte order or a write signal.

The digital component follows Texas Instruments **SNAS534B**, pages 5–6 and
9–11 ([manufacturer datasheet, mirrored PDF](https://pdf.direnc.net/upload/dac0830-dac0832-datasheet.pdf)).
Its input buffer follows the byte bus while ILE=1, CS=0 and WR1=0. The DAC
register follows that buffer while WR2=0 and XFER=0. Otherwise each retains
its value. Both may be open together. Startup contents remain unknown until
supplied or loaded. The model omits analog conversion, propagation delay,
settling, setup/hold constraints and electrical behavior.

[The configuration](dac-output-study.json) records the document fingerprint,
photo, unknown initial contents, pin levels, candidate data sites, and transfer
policy. No board-specific route or control level is built into the CPU model.

## Four candidate byte routes

Replay the existing [sine operand](SINE-OPERAND.md) q3 experiment at all 65
quarter-wave phases. Let S be the actual lookup-ROM byte. Its first paired
result is the 16-bit value `2*(S+5)`; the second is 0002.

| Route hypothesis | ALU-Y source | Data reaching the eight-bit input buffer |
| --- | --- | --- |
| `rom_sum` | 317 | S+5 |
| `first_low` | 392 | `2*(S+5)&FF` |
| `first_high` | 393 | `2*(S+5)>>8` |
| `all_four` | 392–395 | First low, first high, 02, 00 |

All source PCs and bus selections are assumptions. No output-enable predicate
has been promoted to hardware truth.

The narrow bus materially changes the interpretation:

| Phase | ROM byte S | Paired word | Low byte | High byte | Earlier S+5 |
| --- | --- | --- | --- | --- | --- |
| 0 | 0 | 10 | 10 | 0 | 5 |
| 53 | 122 | 254 | 254 | 0 | 127 |
| 54 | 123 | 256 | 0 | 1 | 128 |
| 64 | 127 | 264 | 8 | 1 | 132 |

Values in this table are decimal. The low-byte route drops from 254 to zero
between phases 53 and 54. The high-byte route supplies only zero or one.
Routing all four bytes leaves the input buffer at zero for every phase;
with a transfer after each byte, the phase-dependent first value is followed
by the high byte, 2, and zero. The earlier S+5 route remains monotonic.
These distinguish candidate connections; they do not prove that a discontinuity
is forbidden by the real signal-processing algorithm or analog circuit.

## Load versus transfer

Each source event drives a diagnostic WR1 low/high pulse with data held fixed.
Three explicit WR2 policies are compared:

- Transfer after each load: code updates at cycle 45 for `rom_sum`, 55 for
  `first_low`, 56 for `first_high`, or 55–58 for `all_four`.
- Transfer on the first execution of 084: the output code remains unknown
  until cycle 110, then receives the last buffered byte. Intermediate bytes
  in `all_four` never reach the DAC register under this policy.
- Never transfer: the input buffer is populated, but the DAC register remains
  unknown throughout the run. A logged byte alone is not a conversion event.

Pulses are ordered sub-events within the cited microinstruction; no duration
in seconds or minimum write width is asserted. Idle pin levels and transfer
sites are diagnostic choices. None is inferred from a terminal branch or a
nearby controller handshake.

## Validation and reproducibility

The component passes 8,192 combinations of all five binary control levels and
all 256 data bytes with independently specified old register values. Sequential
tests cover changing data while a buffer is open, retained values when closed,
both buffers open, blocked loading, and transfer before any known input.

All 65 main-runner traces retain their existing sine-study digests. Four routes
and three transfer policies give 780 sink cases. Four full microcode witnesses
at phases 0,53,54,64 include every candidate's pin/state event log. The report
checks the one low-byte drop, each final buffer/register value and exact
transfer-cycle list. The full study reproduces byte for byte; all 105 tests pass.

[Component and adapter](dac0830.py), [runner](dac_output_study.py),
[report](results/dac-output-study/report.json), and
[phase/code table](results/dac-output-study/phase-codes.csv).

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/dac_output_study.py
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -p 'test_*.py'
```

This supplies an assumed digital connection experiment for the plan's DAC
question. Physical strobe qualification, connector wiring, analog scaling,
continuous sample timing and the controller link remain open. Annotation
coverage remains 534 used words.
