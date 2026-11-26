# Full-byte DAC candidate through DSC Tx/Rx and the 8031

The [full-DAC-bus screen](JOINT-MASK04-BUFFERED-DAC-BUS.md) found six
previously frozen, photo-B5-compatible orders that carry the complete
buffered call and answer data with no independent-decoder errors. This
experiment takes the highest-correlation order from that earlier screen,
Y-bit→DAC-code-bit `[4,0,6,1,3,2,5,7]`, and feeds its filtered **full-byte**
output into the real DSC receive PROM. It tests both `127` and `129` as the
candidate latch word. The analog PCM and DAC-code hashes must match the
saved transmitter screen before any receive run starts.

Each selector executes 1,269,256 real-PROM transmit microinstructions.
Each of the four receive cases executes 780,047 real-PROM words. The
independent reference decoder makes 0/64 errors in every case. The frozen
`46/93` PROM-byte readout makes no wrong data decisions but abstains on
three call or five answer dibits at either latch word. The separately
frozen ADC-margin selector has no abstentions but makes one call error at
symbol 45; it is exact for answer.

A **new rule proposed after inspecting those results** takes the `46/93`
decision whenever known and uses the margin selector only for its
abstentions. It does not overwrite any known `46/93` decision. In this
same fixture it recovers all 32 data dibits and the exact eight line
bytes per selector:

| Selector | Latch words | 46/93 wrong/unknown | Margin wrong/unknown | Fixed-first fallback wrong/unknown | Aligned 8031 handoff |
| --- | --- | ---: | ---: | ---: | --- |
| `40` call | `127`, `129` | 0/3 | 1/0 | 0/0 | `AF→B0`, eight zero octets |
| `60` answer | `127`, `129` | 0/5 | 0/0 | 0/0 | `AF→B0`, eight zero octets |

The recovered call bytes are `62 DE 61 9D 7C 5F E5 E2`; answer bytes are
`A5 C2 4C 58 52 47 65 B4`. The paced 8251 and preserved 8031 ROM
consume all eight bytes without overrun or emulator error. Moving the
assumed SYNDET pulse from bit 66 to 65, 67 or 130, or changing the
controller selector, leaves the ROM at `AF` in every case.

This is a complete **conditional full-byte** Tx→analog→ADC→Rx→controller
execution for the zero-run payload. It does not validate the post-hoc
fallback on independent data, identify an onboard decision circuit or
establish the physical DAC/ADC, clock, line and USART/SYNDET nets. The
processors run sequentially under a paced interface model. C2 and C3
remain open. Freeze the fallback now, then challenge it on different
controller bitstreams, gain and timing before treating it as robust.

Run `python3 g2/joint_mask04_buffered_full_bus_loopback.py` from the
microcode directory. The [machine report](results/joint-mask04-buffered-full-bus-loopback.json)
contains source and PCM hashes, complete decision vectors, PROM trace
digests and controller control outcomes.
