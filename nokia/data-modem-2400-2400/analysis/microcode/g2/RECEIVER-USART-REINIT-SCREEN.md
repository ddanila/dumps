# The controller does not reinitialize the line USART at `AF`

The line-side 8251A is programmed in external-SYNDET mode at controller
startup. One possible explanation for the conditional [aligned receive
handoff](RECEIVER-AD-AE-AF-ZERO-HANDOFF.md) is that the 8031 resets or
reprograms that USART just before accepting the remote data segment.
This [write screen](receiver_usart_reinit_screen.py) instruments every
external MOVX write in the existing Timer-1-paced real-ROM `AD→AE→AF`
fixture, then continues through eight received zero-source octets. It
compares the aligned SYNDET pulse with an absent-pulse control for both
scrambler delays.

| Delay | `AE` entry | `AF` entry | First received byte read | Port `05` writes | Port `06` writes | Port `01` writes |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 5 | 6,990 | 58,399 | 114,666 | **0** | 5 | 67 |
| 18 | 6,996 | 58,576 | 114,837 | **0** | 5 | 67 |

The only control-port sequence is `80 00 40 6E 35` at port `06`,
around cycle 630. Port `06` is the DTE-side USART; port `05` is the
line-side USART control port. The 67 port-`01` writes are local
line transmit data and finish before `AF`. The absent-pulse controls
execute the same external writes, but remain at `AF` instead of
advancing to `B0`.

Thus **this executed `AD→B0` path contains no 8031 write that could
restart line-side 8251 character assembly at the remote data boundary**.
The fixture begins at synthetic state `AD`, so it does not exclude an
earlier USART setup, a held SYNDET level, receive-clock gating, or
external sync circuitry. It also projects the remote RxC start at cycle
85,000 and still supplies the successful SYNDET pulse at bit 64. The
physical source and timing of that edge remain open C3 work.

The [machine report](results/receiver-usart-reinit-screen.json) records
the per-port counts, exact control writes, state/receive times,
instrumented-source hash and source hashes. Reproduce from the
microcode directory with `python3 g2/receiver_usart_reinit_screen.py`.
