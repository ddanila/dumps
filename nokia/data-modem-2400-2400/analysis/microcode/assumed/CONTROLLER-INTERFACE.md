# Controller frame and handshake constraints

Local execution of the unchanged 8031 ROM verifies its input/output transfer
routines with byte-distinct frames, changed and unchanged prior state, delayed
completions, and deliberately incomplete transfers. This supplies independent
controller-side constraints for the microcode investigation. It does not
establish that either serial chain connects to DSC2847 or to the DAC.

## Input at 0800

The routine consumes seven synthetic receive-completion events. It discards
the first byte, then stores six payload bytes in RAM 2A–2F, in order. Only
the first payload byte is XORed with 07. RAM bit 22.0 is cleared on entry and
set if any normalized payload byte differs from its previous RAM value.

For example (all values hex):

```
received:      A5 12 34 56 78 9A BC
stored 2A–2F:    15 34 56 78 9A BC
```

All 256 values of the discarded byte leave this stored payload unchanged.
All byte values are also tested at each of the six payload positions, both
against matching prior RAM and against a one-bit difference in that position.
The prior changed flag starts at one, so the matching cases verify that the
firmware actually clears it rather than merely leaving an initial zero.

With handshake bits initially low, the P1 latch sequence is:

1. Set P1.1 before waiting for the discarded byte.
2. After that receive completion, clear P1.1 and set P1.0.
3. Receive and compare/store the six payload bytes.
4. Disable receive, clear receive-ready, and clear P1.0 before returning.

No receive completion leaves the routine waiting at 0807. Supplying only six
of the required seven events leaves it waiting at 087E for the last payload
byte, with P1.0 still high. These are bounded waits, not repaired executions.

## Output at 0899

The routine transmits RAM 30–33 in order, after XOR masks 00,03,00,F8. For
RAM bytes `12 34 56 78`, the observed SBUF writes are `12 37 56 80`.
Every value is tested independently at each of the four source positions.

The firmware first clears P1.0 and P1.2. It waits for each preceding transmit
completion before loading the next byte. After the fourth completion it sets
P1.2, executes a NOP, clears P1.2, and returns. Thus the P1.2 pulse follows
completion of the entire four-byte frame; it is not a per-byte pulse.

With no transmit completions, execution waits at 08B0 after loading the first
byte. Allowing three completions permits all four SBUF writes but leaves
execution waiting at 08D4, with no P1.2 pulse. This negative case distinguishes
“the fourth byte was submitted” from “the frame completed and was latched.”

## Timing experiment and limits

The harness schedules completion events after explicit delays. For the sample
frames above, the local routine durations are:

| Completion delay, harness ticks | Input routine ticks | Output routine ticks |
| --- | --- | --- |
| 8 | 107 | 64 |
| 16 | 163 | 96 |
| 32 | 275 | 160 |

The payload transformations and handshake ordering are unchanged. These tick
counts describe this synthetic completion policy and CPU model. They are not
oscillator measurements, sample rates, serial pin waveforms, or DSP clocks.
Interrupts are disabled in these local probes; the earlier reset-started
controller runs separately exercise Timer 1.

The verified interface contract is six received state bytes, four transmitted
control bytes, normalization masks, a changed-state flag, and explicit transfer
completion before the output latch pulse. Byte order is established at SBUF
and RAM; physical shift-register order and signal meanings remain untraced.
Neither a 16-bit sample grouping nor a controller-to-microcode register mapping
is inferred merely from these frame lengths.

## Implementation and verification

The new [probe](../../interface_probe.c) uses the existing vendored emu8051 core
and hash-checked 8-KiB controller ROM. It starts locally at 0800 or 0899 with
an explicit caller frame; RET reaches an out-of-ROM sentinel that is never
executed. No ROM, CPU-core code, or existing controller harness is modified.
All synthetic inputs and completion assumptions are declared in
[interface-scenario.json](../../interface-scenario.json).

The [study script](../../interface_study.py) runs 4,362 fixtures:

- 3,072 input cases: six positions × 256 values × matching/differing prior RAM.
- 256 discarded-byte cases.
- 1,024 output cases: four positions × 256 values.
- Six delay cases and four incomplete-transfer cases.

All checks pass without CPU exceptions or unexpected MOVX accesses. Incomplete
transfers remain at their expected waits after the 10,000-tick limit. The
[report](../../results/interface-study/report.json) retains 18 event witnesses,
all-fixture/all-execution digests, ROM/source hashes, and assumptions. It
reproduces byte for byte. The existing 61 microcode tests also pass.

```sh
python3 nokia/data-modem-2400-2400/analysis/interface_study.py \
  --out /tmp/nokia-controller-interface
```

The missing physical connection to the microprogram remains an open plan
requirement. These tests constrain a future connection model without creating
one from an arbitrary byte or bit assignment.
