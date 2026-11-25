# ADC-bit decoder screen and waveform-order history at D3F8

The photographed ADC0800 offers a plausible receive-sample source, but its
bus is not traced to the DSC 2847. The [decoder screen](lower_i_d3f8_adc_decoder_screen.py)
therefore feeds **one bit of a complementary reference ADC code** through an
explicit two-level D3F8 decoder, without asserting that this decoder exists
on the Nokia board. It uses the real four-PROM image and the previously tested
`3ED–3FA` loop mapping `I7/A0=!10.6, I0/A1=11.2, lower I6=11.0`, with Q=5
and zeroed RAM. D0 is held high in each candidate code. The ADC code is
`127 - signed PCM sample`; its scale and offset are diagnostic choices.

The stimulus is **32 consecutive samples** (indices 64–95) from the local
reference waveform. The reference decoder recovers its known dibits from the
whole waveform. At the hypothesized 14.4 MHz microinstruction rate, one
9,600 Hz sample spans 1,500 microinstructions. The selected D3F8 site recurs
every eight microinstructions, so the code is held for alternating **188/187
visits**. This tests a continuous changing sample stream rather than a
single pulse. The oscillator-to-microinstruction relation, ADC conversion
clock and D3F8 input path remain untraced.

The [saved screen](results/lower-i-d3f8-adc-decoder-screen.json) covers the
seven code pairs that survived both directions of the earlier held-input
test, all eight ADC output bits and both polarities: **112 cases**. Only
**eight** reach all 6,000 scheduled input visits:

| D3F8 codes | ADC bit and polarity reaching 6,000 visits |
| --- | --- |
| `03/05` | bit 0 normal; bit 4 normal; bit 5 both; bit 6 normal |
| `05/07` | bits 5 and 6 inverted |
| `05/09` | bit 3 inverted |

The other four code pairs have no full-window survivor. A visit count alone
does not show that the ALU selected every offered byte. The
[detailed witness](lower_i_d3f8_adc_history_witness.py) checks that point
for `03/05` bits 0, 4 and 6, and compares each 32-sample forward stream
against the same samples in reverse order. Both then receive **the same
constant `03` for four sample periods** (750 D3F8 visits). All six detailed
runs select the exact 6,750-byte offered stream, reach the end on the same
PC path and end at `3F8`. The shared tail is a controlled held input, not
four additional reference samples.

| ADC bit | Forward/reverse state differences during 750 shared-tail visits | Different selected ROM addresses during tail | Different ALU Y values at `3F8` / `3F9` / `3FA` |
| --- | ---: | ---: | --- |
| 0 | 750 | 1,393 | 643 / 643 / 748 |
| 4 | 750 | 1,393 | 643 / 643 / 750 |
| 6 | 0 | 0 | 0 / 0 / 0 |

The state comparison includes RAM, Q, ALU, next PC and stack at each D3F8
visit. Bits 0 and 4 thus leave **persistent waveform-order history** under
this candidate mapping even after the current input becomes identical.
Bit 6 is a useful control: it consumes the same length of changing input but
leaves no difference in the shared tail. The [saved witness](results/lower-i-d3f8-adc-history-witness.json)
records source hashes, trace digests and comparison counts.

This narrows the receive-side search; it does **not** identify a demodulator
or satisfy C3. Only one bit of each sample is offered, the two-level decoder
and D0 bias are untraced, and the changed ALU Y values have no verified route
to a receive decision or USART-01 RxD.

The [cross-symbol screen](lower_i_d3f8_adc_cross_symbols.py) then tests all
eight 32-sample survivors against six different repeated four-dibit patterns.
The independent reference receiver recovers each complete pattern. In the
[saved 48-case matrix](results/lower-i-d3f8-adc-cross-symbols.json), the
original `0,1,3,2` pattern keeps all eight candidates in D3F8, but the other
patterns keep only one to five. The `03/05` bit-0 candidate is the most
consistent of the earlier history witnesses, reaching the full 6,000 visits
for four of six patterns. Bit 4 reaches the full window only for the original
pattern. Every short-window exit in this fixture proceeds into the repeated
`1E9/1EA` path described by the [exit-path analysis](LOWER-I-EXIT-PATH.md).

For the four patterns that bit 0 carries through 32 samples, the same screen
extends the window to **128 samples** (24,000 scheduled D3F8 visits). All
four leave D3F8 after **6,002–10,690 visits** and spend the rest of the run
at `1E9/1EA`; none reaches a demonstrated receive decision. These are
constraints on this **mapping, initial state, one-bit decoder and assumed
clock**, not proof that the ADC cannot feed a different receiver path. The
next test should change a concrete timing or input-route hypothesis that
can sustain multiple symbol sequences and pass through a candidate decision
or output event. A decision must then be compared with known dibits under
different sequences and phases, and its route toward USART-01 RxD checked.
