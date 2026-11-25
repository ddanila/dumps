# One candidate DAC bus carries recoverable controller dibits

The [full-stream PROM replay](PHOTO-MAIN-DIBIT-PULSE.md) verifies every
PC129 ROM address and Am2901 Y byte through 24 or 32 real controller dibits
per class. This [output-route screen](photo_main_dibit_dac_decode.py)
reconstructs its candidate 9,600-sample/s DAC bytes from that checked
recurrence, and verifies the **SHA-256 of every sample byte** against the
PROM-run report before comparing alternatives. It keeps the photographed
74LS273 Q4→DAC08 B5 candidate segment and tests three simple Q→B orders,
with ordered or Y7/Y4-swapped Am2901 Y→latch inputs. Only the one B5 segment
is photo-suggested; the complete bus and capture clock are untraced.

An independent [V.26-class reference receiver](reference_modem.py) then
processes each candidate code stream. It has a known carrier and a timing
offset of four samples (half of the assumed eight samples/symbol), held
fixed across the four controller classes and all bus orders. The decoder
uses a raised-cosine matched filter and differential decisions; it is **not**
the Nokia DSC receiver.

| Y→74LS273 D | 74LS273 Q→DAC08 B | Wrong dibits / 104 | Mean absolute waveform correlation with reference |
| --- | --- | ---: | ---: |
| Ordered | Reverse | 74 | 0.053 |
| Ordered | Rotate by one | 31 | 0.322 |
| **Ordered** | **Exchange Q4/Q5** | **1** | **0.701** |
| Exchange Y7/Y4 | Reverse | 72 | 0.095 |
| Exchange Y7/Y4 | Rotate by one | 69 | 0.077 |
| Exchange Y7/Y4 | Exchange Q4/Q5 | 71 | 0.061 |

The Q4/Q5 bus has one error in 30 decisions for selector `00`, at the first
decision near the start of the finite stream. It has **zero errors in 74
held-out decisions** from selectors `20`, `40` and `60`. Selecting the bus
using only `00` picks this same mapping. With the selected bus but **no dibit
pulses**, the same decoder makes 74 errors in 104 decisions and emits zero
dibits. Thus the recovered data depends on the controller-driven phase
changes, not merely on the carrier or reference decoder.

The four-sample timing was chosen after a bounded eight-offset screen. For
the selected bus, offset 0 gives 60/108 errors; offsets 1–7 give 42, 13, 3,
**1**, 3, 7 and 24 errors out of 104. The result has a small timing window
rather than a single isolated alignment. The
[machine report](results/photo-main-dibit-dac-decode.json)
records every bus/class decision count, mismatch index, timing result,
correlation and source hash.

This is strong **conditional transmitter evidence**: one simple,
photo-compatible output mapping carries nearly all real controller dibits
in a form independently decodable as differential phase. It does not prove
the four-visit USART pulse, the seven other DAC wires, the LS273 clock, the
analog line route, pulse shaping, or segment-1 reversals. The reference
receiver result does not satisfy G2's DSC receive/echo requirement. Next
constrain the latch data/clock from the photos and test segment-1 reversals;
keep alternative output and shaping paths live, especially for the selector
`20` spectrum mismatch.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/photo_main_dibit_dac_decode.py
```
