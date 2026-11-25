# Conditional segment-1 to segment-2 continuity in one DSC run

The [interrupt-paced 8031 run](MAIN-LOOP-TIMER1-SEGMENT2.md) emits no
port-01 data during A3, then emits the exact V.26 ter segment-2 GPC/GPA bits
in A4/A5. The [literal A3-frame test](PHOTO-A3-HELD-FRAME-SEGMENT1.md) does
not produce the required repeated 180° reversals. This
[continuous replay](photo_segment1_to_segment2_continuous.py) tests a different,
**untraced** source: a decoder or idle circuit offers dibit `11` for 32 A3
symbols, then offers the recorded A4/A5 dibits without resetting the DSC.
An unmodulated `00` idle source is the control. Both use the same q3 mapping,
upper PROM bank, four-visit D127 pulse, swapped serial-bit lanes and candidate
Y129 DAC capture used in the
[segment-2 calibration](PHOTO-SEGMENT2-STANDARD-CALIBRATION.md).

| Controller selector | A3 input hypothesis | A3 carrier-relative phase | Errors in 62 aligned decisions |
| --- | --- | --- | ---: |
| `40` / GPC | repeated `11` | `128, 0` repeated 16 times | **0** |
| `40` / GPC | unmodulated `00` control | `0` for all 32 symbols | 31 |
| `60` / GPA | repeated `11` | `128, 0` repeated 16 times | **0** |
| `60` / GPA | unmodulated `00` control | `0` for all 32 symbols | 31 |

Each row executes **768,256 real-PROM microinstructions** in one 64-symbol
run and checks **192,054** PC129 ROM reads and ALU Y values. The selected
DAC-bus sample digest matches an independent reconstruction. All 12
photo-B5-compatible DAC bus orders give the reported decision count. The
phase offset is zero at both the last A3 symbol and first A4 symbol; the
actual carrier continues through the boundary. The `00` control still
decodes the A4 pattern, so its 31 errors are confined to the missing A3
half-turns in the aligned decision window.

This is evidence that one *candidate* microcode path can carry both training
segments continuously under the stated inputs. The controller does not emit
the hypothetical A3 dibits in port-01 writes. The
[8251A sync-fill audit](USART-SYNC-FILL-SEGMENT1.md) now gives a concrete
candidate source: programmed `FF` sync characters automatically transmitted
while the USART data buffer is empty. **This replay omitted the first A4
serial bit** between its 64-bit fill and standard segment-2 windows, so it
does not prove raw TxD continuity at the boundary. The actual fill duration,
D127 pulse gate, DAC latch clock/bus and analog line route remain assumptions.
The matched-filter decisions are made by an
independent reference decoder, not the DSC receiver. C2, C3 and C4 remain
open. The next test should resolve the bridge bit's symbol timing and
candidate input pairing, with the `FF`-fill USART behavior made explicit.
Missing net continuity does not block that experiment. The
[machine report](results/photo-segment1-to-segment2-continuous.json) records
the four traces, sample digests, phase checkpoints, bus scores and source
hashes.
