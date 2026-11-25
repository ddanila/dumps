# The controller recognizes eight received zero octets in state AF

[V.26 ter §6.3.1.3](https://www.itu.int/rec/dologin_pub.asp?id=T-REC-V.26ter-198811-I%21%21PDF-E&lang=e&type=items)
requires detection of 64 consecutive received scrambled binary zeros during
the echo-cancellation sequence. The controller ROM has a matching,
state-specific path. State `AF` dispatches at `08E9` to `0A4E`, which reads
USART-01 status/data through `1DB8`, descrambles at `05A3`, then calls the
zero-octet counter at `1BBB`. Its state step at `1319–1325` advances to `B0`
when RAM63 reaches eight.

The [preserved-image execution](zero_run_detector.py) uses a nonzero 23-bit
scrambler history, generates distinct line bytes with the independently
verified five- and eighteen-bit V.26 ter polynomials, and offers each byte
at the modeled USART-01 MOVX reads. Every byte enters through the actual
ROM dispatcher; the test checks one status and one data read, the decoded
octet and the running count. After the last byte, it directs the same 8031
image to the `1000` state step.

| Decoded sequence | RAM63 after final byte | State after step, both polynomials |
| --- | ---: | --- |
| Seven `00` octets | 7 | `AF` |
| Eight `00` octets | 8 | `B0` |
| Seven `00`, then `01` | 0 | `AF` |
| Eight `FF` octets | 0 | `AF` |
| Seven `00`, `01`, seven `00` | 7 | `AF` |
| Seven `00`, `01`, eight `00` | 8 | `B0` |

The line bytes are genuinely scrambled rather than eight literal zero
bytes: with the five-bit polynomial, the first eight zero-source octets
arrive as `62 DE 61 9D 7C 5F E5 E2`; with the eighteen-bit polynomial,
they arrive as `A5 C2 4C 58 52 47 65 B4`. The
[saved report](results/zero-run-detector.json) records all 12 runs and
source hashes.

This is a strong controller-side match to the standard's 64-zero step and
narrows the likely role of state `AF→B0`. The ROM implementation counts
whole zero octets; this test does not establish detection at every possible
bit alignment. The harness supplies modeled USART reads and explicitly
starts the final state step, so it does not prove a naturally timed call,
physical DSC receiver output, or that `B0` activates the echo canceller.
