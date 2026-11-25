# Executed controller state frames reach a candidate DSC byte relay

The [joined 8031 run](RECEIVED-CHAIN.md) receives a synthetic USART packet,
steps the A0–A2 state chain and emits four four-byte frames on one preserved
controller image. The [bridge execution](received_chain_microcode.py) takes
one representative from each of its four RAM2E bit-6/bit-0 classes (`00`,
`01`, `40`, `41`), repeats that class's 16 outgoing bytes eight times, and
offers them at the **assumed** DSC2847 D-input word `38E`. It executes the
real four DSC control PROMs, Am27S31 dump and separate-slice Am2901 candidate
with initial Q=5.

All four 1,580-microinstruction runs finish cleanly and select 128 offered
bytes. Each reaches `39E` 128 times. Its ALU Y follows the independently
derived one-visit relay rule
`Y39E[n] = 0x1B + 2 × (D38E[n−1] & 0x70)` after the startup value `FB`.
The selected ROM read stays at `1F6` in all four cases.

| Received selector difference | Controller frame difference | `39E` output visits that differ |
| --- | --- | ---: |
| `00` vs `01` (bit 0) | `D0`→`C0` in the last two frames | 16/128 |
| `00` vs `40` (bit 6) | Fourth byte `22`→`BA`, then `EA`→`BA` | 15/128 |

Thus the executed controller receive byte changes the emitted frame, and
those exact bytes change a reached DSC ALU value under this connection
hypothesis. This is an end-to-end **conditional byte sensitivity** result,
not a recovered DSP command: the four-byte output's physical destination,
the D38E route and timing, and any `39E`-to-DAC latch path remain untraced.
Repeating the frames is a diagnostic stimulus, not a real call. The ROM read
does not advance and the `39E` values are not a modulated line signal.

The [report](results/received-chain-microcode.json) records the frames,
output bytes, pairwise differences, ROM addresses, trace digests and source
hashes.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/received_chain_microcode.py
```
