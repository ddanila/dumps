# ADC0800 receiver-input candidate on DED 3558

The [DED 3558 front photograph](../../../photos/PXL_20261123_114854803.jpg)
shows a stickered 18-pin device marked **ADC0800PCD** near the lower middle of
the board. The marking is legible in the original image around pixels
`x=1500–1650, y=2780–3080`. This is an observed part marking, not a traced
connection to DSC 2847. The adjacent digital traces and buffers make a
byte-wide receiver-input route plausible; their individual nets remain
unmeasured.

The [National Semiconductor ADC0800 datasheet](https://www.ee.iitb.ac.in/student/~wel/wel12/Components%20Records/analog%20ic_datasheet/adc0800.pdf)
identifies the `PCD` variant as an **8-bit A/D converter**. It performs
successive approximation internally, latches the result, and exposes
tri-state **complementary binary** outputs. The data outputs are pins 4, 3,
2, 1, 17, 16, 14 and 13 from MSB to LSB; analog input is pin 12, start
conversion pin 6, end-of-conversion pin 9, output enable pin 7 and clock pin
11. The datasheet specifies 40 converter-clock periods per conversion and
gives 50 µs as its typical conversion time. These are component properties,
not measured timing on the Nokia board.

This corrects an earlier receive-path hypothesis in [PLAN-2](../PLAN-2.md):
the photographed ADC can supply a parallel sample byte without a microcoded
SAR loop built from an external DAC and comparator. The complementary coding
also matters for any receiver stimulus: a natural binary reference sample
cannot be presented unchanged as a raw ADC0800 output byte. The analog
reference range, sample timing, bus buffer, output-enable route and DSC 2847
D-input connection are still unknown, so no ADC sample is yet claimed to
reach the microprogram.

In the same photograph, two **SN74LS244** buffers sit immediately beside the
ADC0800, with front-side traces running from the converter's pad region toward
their pad regions. The [TI SN74LS244 datasheet](https://www.ti.com/lit/ds/symlink/sn74ls244.pdf)
identifies these as noninverting octal buffers with three-state outputs and
separate output enables. An ADC→buffer→board-bus path is therefore a concrete
photo-supported candidate, but the individual bit connections, enable pins
and receiving connector pins have not been identified. The ADC's own latched
outputs also mean that a candidate microcode loop should normally see a held
conversion byte until a new conversion completes, rather than a new sample
on every microinstruction.

The [held-byte 187 probe](adc_hold_187.py) tests that timing alternative in
the fitted-swapped mapping. Across both Q=1 and Q=129, all 256 byte values
run cleanly for 512 cycles. Only byte `00` exits the 187/188 PLP/BLT loop to
084; every nonzero byte ends in that loop, although some briefly take other
PCs and reenter. Representative nonzero values end there after 4,096 cycles.
This makes the earlier per-visit
sample-order effect at 187 a poor receiver lead under a plausible ADC hold.
The [saved result](results/adc-hold-187.json) is still a wiring hypothesis,
not an observed ADC-to-DSC connection.

Earlier documents called the photographed DED 3558 converter a `DAC0830`.
The visible sticker instead reads `ADC0800PCD`; a DAC0830 on this board has
not been identified from this photograph. A separate **DAC08HP** marking is
visible in the lower analog section of the same board; see the
[output-converter evidence](DAC08-OUTPUT.md). The existing
[DAC0830 model](../assumed/DAC-OUTPUT.md) remains a diagnostic output
hypothesis, not the identified board converter. A transmitter demonstration
still needs the DAC08 input-byte/strobe route and changing line codes.
