# A candidate late loop mixes an 8031 frame byte with its line bits

The [late-byte relay](LOWER-I-LATE-BYTE-RELAY.md) found a D-selected input at
`3A6` that changes four internal Y captures. The preceding `3A4` also selects
external D. The [two-input runner](lower_i_command_data_mix.py) puts a held
controller frame byte at `3A4` and serial line bits at `3A6`, after the same
labelled D3F8 trigger and under the same read-valid PROM-data and
previous-carry hypotheses. The controller frame could be held by the four
photographed CD4094 registers, but their outputs and both DSC D routes are
untraced.

For `m = D3A4 & 0F` and `n = D3A6 & 0F`, the real-PROM execution produces
this exact Y quartet at `3B3, 3B4, 3B5, 3B6`:

```text
(F0 | n, F0 | ((m + n) & 0F), n, 0F - n)
```

The runner executes every 16×16 low-nibble pair for 512 cycles and checks
all 14 reached quartets per pair. It separately executes all 256 held-frame
byte values with line D=`01`, confirming that the frame byte's high nibble
has no effect in this fixture. These 512 checks establish the arithmetic
rule within the tested entry state; they do not establish physical input
pins or DAC wiring.

The input bytes then come from the [uninterrupted 8031 main-loop runs](MAIN-LOOP-SERIAL.md),
which preserve the controller image through receive, state, frame-send and
USART-01 line-output routines. Four representative selector classes supply
their actual LSB-first line bytes. For each class, the held `3A4` byte is
**frame lane 1 at the first line-output iteration**; that lane remains `47`
or `42` for the rest of the recorded 12-iteration run.

| Selector | Held frame lane 1 | Real line bits checked | Captured effect |
| --- | --- | ---: | --- |
| `00` | `47` | 64 | All 64 quartets follow the two-input rule |
| `20` | `47` | 64 | All 64 quartets follow the two-input rule |
| `40` | `42` | 48 | All 48 quartets follow the two-input rule |
| `60` | `42` | 48 | All 48 quartets follow the two-input rule |

A separate 224-bit concatenation keeps the DSP state across those four
streams and follows the same rule at every bit. That concatenation is a
diagnostic, not one uninterrupted controller call. To isolate the held-frame
effect from the differing line streams, the runner replays the same 64 line
bits twice with `3A4=47` and `3A4=42`. **Only the `3B4` Y byte changes,
on all 64 visits**; `3B3`, `3B5` and `3B6` remain equal. This is a conditional
command-byte and line-bit arithmetic mix in the executed microcode.

The [machine report](results/lower-i-command-data-mix.json) contains the
exhaustive-check counts, controller frames and bytes, class and crossed
traces, source hashes and the exact rule. The D3F8 trigger, CD4094 output
order, D3A4/D3A6 connections, flag source and `3B3–3B6` capture assignment
are hypotheses. The quartet has no verified DAC input or carrier samples;
the [direct-clock screen](LOWER-I-LATE-DAC-CLOCK.md) also excludes its simple
fixed-site clocks at the hypothesised 9,600-sample/s cadence. G2's C2 and
C3/C4 acceptance tests remain unmet. The next useful run needs a
photo-compatible route from this or another stateful path to the DAC and a
line-rate sample clock, or a receive decision traced from ADC input.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/lower_i_command_data_mix.py
```
