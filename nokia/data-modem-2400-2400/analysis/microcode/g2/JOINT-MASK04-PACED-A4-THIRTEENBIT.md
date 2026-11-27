# Paced controller A4 TxD survives the frozen thirteen-bit DSC receiver

The prior [single-run demonstration](JOINT-MASK04-END-TO-END-DEMO.md)
executed the 8031 scrambler byte by byte but assumed how those octets
were shifted by USART 01. This [call/answer challenge](joint_mask04_paced_a4_thirteenbit.py)
instead starts from the saved [17-character paced 8251/8031 execution](MAIN-LOOP-USART-TXREADY-17.md).
Across eight sampled Tx-clock phases per selector, that execution
produces the same first eight line-side A4 bytes aligned from bit 1 of
the first shifted character:

| Selector | Eight paced A4 line bytes | Frozen receiver |
| --- | --- | --- |
| Call `40` | `FC 03 7C 0E 0E F8 C0 18` | 0/64 wrong dibits; all eight line bytes exact |
| Answer `60` | `FC 03 7C CE 07 E1 84 EC` | 0/64 wrong dibits; all eight line bytes exact |

An explicitly assumed one-symbol pair buffer translates those shifted
TxD bits into D127 pulses. The q3/mask-`04` emulator executes the real
PROM transmitter and receiver at carrier offset 203, with the same
photo-compatible DAC bus, Q=0.5 line filter, 0.85× receive level and
late `81→A1` mode edge as the earlier holdout. Both A1 windows peak at
2,100 Hz. Neither receiver waveform clips; the independent reference
and the **unchanged frozen thirteen-bit phase gate** make zero wrong
dibit decisions. Both runs reach state `1909`, which was absent from
the gate's 159-state fit. The modeled 8251 receive path returns the
eight paced line bytes with zero status errors.

For an additional controller check, the receive probe starts from its
declared descrambler history `5A1234`. Its unchanged 8031 ROM produces
the eight independently predicted probe-history bytes in both modes.
Because the A4 line stream begins at bit 1 of a controller character,
these probe-history bytes are **not claimed to be the original A4
plaintext** from the transmitting controller.

The [call report](results/joint-mask04-paced-a4-thirteenbit.json) and
[answer report](results/joint-mask04-paced-a4-thirteenbit-answer.json)
are source-hashed. This replaces the transmit-byte stimulus with actual
modeled TxD shift events, but the 8251 clock and CTS fixture, TxD pair
buffer, D127 net, DAC/ADC/analog route, receiver capture/gate and
RxD/RxC/SYNDET wiring remain assumptions. It is stronger conditional
end-to-end evidence; C2, C3 and G2 remain open until their physical
routes and gate implementation are constrained.

The same frozen route also passes the [next eight paced A5 bytes](JOINT-MASK04-PACED-A5-THIRTEENBIT.md)
in separate DSC runs for call and answer. The continuous A4→A5 DSC
boundary remains to be tested.
