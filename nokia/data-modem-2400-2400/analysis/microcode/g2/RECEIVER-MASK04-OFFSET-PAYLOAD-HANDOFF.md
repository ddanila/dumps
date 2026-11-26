# Fresh scrambled payloads survive ±7 Hz in the conditional receive path

The [ADC-margin selector](RECEIVER-MASK04-ADC-MARGIN-SELECTOR.md) recovered
one seeded 64-data-symbol stream across ±7 Hz carrier drift. This
[challenge](receiver_mask04_offset_payload_handoff.py) keeps its three
capture pairs, frozen decision tables and selection rule unchanged. It
generates two new complete nonzero eight-byte payloads, scrambles them
with the executed controller polynomials, and sends each through the
real four-PROM mask-`04` receiver for 768,047 instructions. The first
case uses −7 Hz and the call-side delay; the second uses +7 Hz and the
answer-side delay. The independent reference receiver accepts both PCM
streams before PROM execution.

| Delay / offset / phase | Payload | Recovered line bytes | Dibits |
| --- | --- | --- | ---: |
| 5 / −7 Hz / 75° | `95 A5 1A 85 52 4B 62 9E` | `57 1D A3 7A B3 8C 0E 06` | 63/63 |
| 18 / +7 Hz / 165° | `CB 04 D4 40 5B C2 43 FD` | `6E C6 34 6E EB 60 59 0B` | 63/63 |

The selector makes **0 wrong and 0 unknown decisions** among 126
measurable dibits. It selects all three visit pairs in both streams,
including the late 94/141 pair 20 and 25 times. The reconstructed
line bytes exactly match the offered bytes. With an assumed external
SYNDET pulse immediately before data bit 64, the paced 8251 receive
model delivers all eight bytes without overrun and the unchanged 8031
ROM descrambles each exact payload. A one-bit-early pulse, a one-bit-late
pulse, or the opposite descrambler selector fails to recover it.

This shows that the **conditional** PROM receive readout and controller
handoff can handle new full payloads during the V.26 ter ±7 Hz carrier
offset, rather than only fixed carrier rotations or one development
sequence. It does not establish the Nokia circuit that compares ADC
magnitudes, chooses capture phases, serializes dibits, drives RxD/RxC,
or supplies SYNDET. This fixture also does not drive the `81→A1` frame
edge into the PROM. C3 remains open. A photo-compatible clock/latch and
serializer route remains the next test; missing continuity alone does
not block that work.

The [machine report](results/receiver-mask04-offset-payload-handoff.json)
records PROM and ADC hashes, each selected visit pair, USART/8031
outcomes, controls and source hashes. Reproduce from the microcode
directory with `python3 g2/receiver_mask04_offset_payload_handoff.py`.
