# The 8251A sync filler is a concrete A3 segment-1 source

The unchanged 8031 startup code at `1E1E–1E24` sets USART port `05` to mode
`CC`, sync character `FF`, and command `15`. The
[programming-helper execution](../../controller/PROGRAM.md) verifies that
this call writes `80 00 40 CC FF 15`. `CC` selects synchronous, eight-bit,
single-character sync transmission; `15` enables the transmitter without
send-break. The [Intel 8251A datasheet](https://deramp.com/downloads/intel/8251A.pdf)
specifies that, once transmission has started, an empty synchronous
transmitter automatically inserts its programmed sync character into TxD.
Thus, **if CTS permits transmission and the Tx clock runs**, an A3 interval
with no data writes offers repeated `FF` characters: serial `1` bits, or
dibit `11` on every two-bit symbol. Dibit `11` is the V.26 ter 180°
reversal used by the segment-1 target.

The [executed controller audit](usart_sync_fill_segment1.py) reruns both
interrupt-paced `40`/GPC and `60`/GPA paths. It finds no port-`05`
reprogramming in A1–A5, no port-`01` data writes in A3, and the same eight
A4 bytes plus first A5 byte previously recorded. Under an eight-character
`FF` fill window, the first **64 serial bits are all ones**, followed by one
additional bit from the first A4 byte and then the exact **64-bit standard
segment-2 pattern**:

| Selector | Eight `FF` characters | First A4 bit | Following 64 bits |
| --- | --- | ---: | --- |
| `40` / GPC | 64 ones = 32 repeated `11` dibits | `1` | exact GPC segment 2 |
| `60` / GPA | 64 ones = 32 repeated `11` dibits | `0` | exact GPA segment 2 |

This identifies a **specific USART mechanism** for the idle `11` input used
in the [continuous DSC PROM replay](PHOTO-SEGMENT1-TO-SEGMENT2-CONTINUOUS.md).
That replay concatenated 32 `11` symbols directly with the 32 standard
segment-2 dibits. It omitted the first A4 bit shown above; its 0/62 decision
result therefore proves capacity for those two windows, **not** exact
bit-for-bit continuity of raw TxD across their boundary. This one-bit bridge
must be carried through a timing-aware USART-to-DSC model or justified by a
measured decoder/clock alignment before claiming a complete transmitter.

The audit also pairs 128 **contiguous raw TxD bits** from each of the two
possible starting bit offsets within this window and scores them against
the 64-symbol segment-1/segment-2 target. All 12 previously surviving
candidate DAC bus orders agree:

| Selector | Pair at bit 0 | Pair at bit 1 |
| --- | ---: | ---: |
| `40` / GPC | 15/62 errors | **0/62** errors |
| `60` / GPA | 16/62 errors | **1/62** errors |

The bit-1 GPC case is identical to the earlier 768,256-word real-PROM run.
The bit-1 GPA case was separately executed for **768,256 PROM words** with
192,054 checked PC129 ROM/Y visits; the selected-bus sample digest matches
its reconstruction. The bit-0 scores use the same validated ROM/Y model but
were not separately executed. At bit 1, GPA's first A4 `0` replaces the
last `1` required by a full 32-symbol segment-1 window. Thus a fixed pairing
of this specific raw window does not give a perfect transition for both
selectors. This is a precise limit of the present candidate; the actual
symbol boundary and fill count remain unmeasured.

The 8031 main-loop fixture begins after startup, so its unchanged port-`05`
state depends on the separately verified startup programming call. CTS, Tx
clock, physical TxD-to-DSC wiring, actual count of fill characters and the
DAC-to-line route remain untraced. The
[machine report](results/usart-sync-fill-segment1.json) retains both executed
controller checks, byte/bit windows and source hashes. The next experiment
should feed the **raw 8251 bit sequence including the bridge bit** into a
photo-compatible clock/bit-pairing candidate and compare the resulting DSC
phase and DAC samples.
