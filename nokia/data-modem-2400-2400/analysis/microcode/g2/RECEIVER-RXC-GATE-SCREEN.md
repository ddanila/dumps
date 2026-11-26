# Held SYNDET plus gated RxC is a conditional receive route

The controller [does not reinitialize line-side USART control port `05`](RECEIVER-USART-REINIT-SCREEN.md)
in the executed `AD→AE→AF` receive fixture. Intel's [8251A datasheet](https://deramp.com/downloads/intel/8251A.pdf),
page 7, says a positive-going external SYNDET input makes the USART
start assembling data on the next rising RxC edge. Once synchronized,
the high input may be removed. This permits a different wiring
hypothesis: SYNDET is asserted before the receive segment, and **RxC
is gated off during the reversal preamble**, then enabled on the
first data bit.

The [gate screen](receiver_rxc_gate_screen.py) changes only the narrow
8251 receive model: it ignores RxC edges before a chosen gate-opening
bit and latches synchronization on the first enabled edge. It feeds
the preserved 8031 ROM four saved nonzero first-byte streams and two
saved zero-run streams, each already recovered by a real DSC PROM run.
The six bit-64 gated results are byte-for-byte and cycle-for-cycle
identical to the earlier bit-64 SYNDET-pulse results.

| RxC first enabled at bit | Result across six streams |
| ---: | --- |
| 0, start of preamble | Preceding `FF` characters are consumed; neither zero-run case reaches `B0` |
| 63, one bit early | Full consumed stream differs from the offered eight bytes |
| **64, first data bit** | **All eight line bytes consumed exactly; zero-run cases reach `B0`, nonzero cases remain at `AF`** |
| 65, one bit late | Full consumed stream differs from the offered eight bytes |
| 128, never | No received bytes |

For the two payloads whose first data line byte is `FF`, the first
character can look correct even when the gate opens early; comparing
the **whole** eight-byte stream exposes the misalignment. This gate
route is therefore payload-independent under the fixture, but it has
the same strict bit-64 boundary requirement as the pulse route.

The board has no traced SYNDET level, RxC gate, or receive-boundary
driver. The model assumes SYNDET makes a positive transition after
USART setup and before the first enabled RxC edge; a permanent high
from power-up is not demonstrated to satisfy that condition. The DSC
PROM streams are reused rather than rerun, and the 8251 model remains
narrow. C3 stays open. The [machine report](results/receiver-rxc-gate-screen.json)
records all six streams, five gate timings, controller outputs and
source hashes. Reproduce with `python3 g2/receiver_rxc_gate_screen.py`.
