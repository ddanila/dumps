# Received controller byte survives through state selection and outgoing frames

The [received-chain execution](received_chain.py) joins the 8031 USART
receive routine at `0800`, four state-expiry steps at `1000`, and four
four-byte sends at `1EE2` on **one preserved RAM/SFR image**. A synthetic
seven-byte received packet carries each of the 256 possible values in the
fifth payload position. The ROM stores it at RAM2E. The harness then starts
RAM34 at A0, supplies qualification and expiry events, and directs PC to
each state and send routine. Those handoffs remain synthetic.

All 256 runs receive seven bytes and complete four sends without emulator
errors. The resulting state/frame signatures form exactly four classes,
selected by RAM2E bits 6 and 0:

| RAM2E bits 6,0 | State chain after expiry | Distinguishing outgoing frame |
| --- | --- | --- |
| 0,0 | A1 → A2 → B8 → B4 | B8: `D0 42 81 22` |
| 0,1 | A1 → A2 → B8 → B4 | B8: `C0 42 81 22` |
| 1,0 | A1 → A2 → A3 → A4 | A3: `D0 42 81 BA` |
| 1,1 | A1 → A2 → A3 → A4 | A3: `C0 42 81 BA` |

The run independently repeats the older direct-RAM2E chain and compares all
256 results. State transitions and transmitted bytes match exactly. The
first A0 state step takes one extra emulated cycle after the receive routine;
later step counts match. This confirms that, under the stated fixture, a
USART-received byte controls the controller's branch and outgoing frame, and
that the direct-RAM probe did not invent that relationship. It does not
identify the frame's physical recipient or its tone/training/data meaning.

The [report](results/received-chain.json) includes all 256 chains and source
hashes. No DSC2847 microcode or analog line signal is run in this probe.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/received_chain.py
```
