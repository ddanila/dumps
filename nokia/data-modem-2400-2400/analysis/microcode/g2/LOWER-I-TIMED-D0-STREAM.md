# A single-bit D3F8 route carries a clock-matched 8031 stream into ROM arithmetic

The [two-nibble screen](LOWER-I-NIBBLE-STREAM-BRIDGE.md) found three
diagnostic encodings that keep the `3ED–3FA` loop active for all 128 locally
executed 8031 scrambler bits when one bit is offered every loop visit. The
`8/9` encoding is simpler than the other pairs: D3F8 D3 is held high,
D2/D1 low, and **only D0 changes with the bit**. `9/8` reverses its polarity.
The input wire, held levels, Q=`05` startup and paired PROM/latch control
routes are still untraced hypotheses.

The [timed replay](lower_i_timed_d0_stream.py) holds each of those bytes for
the loop-visit count implied by a 2,400 bit/s data stream if a microcycle
takes `k` periods of the board's 14.4 MHz oscillator. The executed loop has
eight microcycles per D3F8 visit, giving `750/k` visits per bit. The
`k=4` half-visit case uses alternating 187/188 holds as well as a diagnostic
constant 188 hold.

| Zero/one D3F8 byte | Hold (visits/bit) | Clock case | Consumed / offered visits | Full 128 bits? |
| --- | ---: | --- | ---: | --- |
| `08/09` | 188 fixed | approximate `k=4` | 24,069 / 24,064 | Yes |
| `09/08` | 188 fixed | approximate `k=4` | 24,069 / 24,064 | Yes |
| either polarity | 187/188 or 188/187 alternating | exact-average `k=4` | 5,628–19,878 / 24,000 | No |
| either polarity | 250 | `k=3` | 2,253–13,253 / 32,000 | No |
| either polarity | 375 | `k=2` | 4,878–33,753 / 48,000 | No |
| `08/09` | **750** | **`k=1`** | **96,005 / 96,000** | **Yes** |
| `09/08` | **750** | **`k=1`** | **96,005 / 96,000** | **Yes** |

Both `k=1` witnesses remain in the ROM loop after the last offered bit. In
a separate traced first-four-bit window (`0,0,0,1`), all 3,000 offered D3F8
bytes are actually selected by the Am2901 instruction and consecutive
visits are eight microcycles apart. For `08/09`, the first changed bit alters
ALU Y at `3F8` on input visit 2,250, Y at `3F9/3FA` on visit 2,251, and the
selected `3F7` ROM address on visit 2,252. During the next 750 visits,
`3F8` Y differs from the held-zero control 688 times and the ROM address
748 times. The inverse polarity also changes the ROM and all three ALU
sites. This is a timed, controller-dependent **internal computation** under
the explicit connection and clock hypotheses.

The [machine report](results/lower-i-timed-d0-stream.json) records all 12
clock/polarity schedules, selected-input checks, first-change timing, trace
digests and source hashes. The 8031 scrambler is run locally; its USART
output is not physically traced to D3F8, and the sequencer divider is
unmeasured. No DAC08 input bytes, latch clock, line carrier, or receive bit
has been identified. The next decisive experiment is to carry the repeated
ROM/ALU values into a photo-compatible output-latch model and test the
resulting DAC-bit stream against the 1,800 Hz and dibit-phase criteria.
