# 8031 controller studies (810244E)

These studies run the unchanged controller ROM in the [8031 harness](../run.py)
and check individual routines against independent reference models. The study
scripts live one level up (`../controller_*_study.py`) and write their reports
to [`../results/`](../results/).

| Topic | Study | Routine(s) |
| --- | --- | --- |
| Line-side data | [SCRAMBLER](SCRAMBLER.md): V.26 ter-style 23-bit scrambler/descrambler | 053E, 05A3 |
| Peripheral setup | [PROGRAM](PROGRAM.md): 8251 reset, mode and command sequences | 1D05 |
| Serial frames | [INTERFACE](INTERFACE.md): mode-0 frame order, XOR masks, P1 handshake | 0800, 0899 |
| Input decoding | [DECODE](DECODE.md): stateful decoding of received bytes 2A–2F | 0620 |
| Events | [EVENT](EVENT.md): countdown-weighted event qualification | 1760, 1790 |
| Output bytes | [OUTPUT-PAIR](OUTPUT-PAIR.md) (bytes 1–2), [OUTPUT32](OUTPUT32.md) (byte 3), [OUTPUT](OUTPUT.md) (byte 4: state code + flags) | 0266–0430, 012F, 006E |
| Output pipeline | [OUTPUT-BUILD](OUTPUT-BUILD.md), [OUTPUT-SEND](OUTPUT-SEND.md): construction through transmission | main loop |
| External read | [READ](READ.md): the repeated 8004 read result is discarded | 08DD |

For how these fit the modem as a whole, see the [device README](../../README.md)
and [PLAN-2](../microcode/PLAN-2.md).
