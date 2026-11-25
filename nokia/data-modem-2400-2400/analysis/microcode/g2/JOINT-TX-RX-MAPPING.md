# Current transmitter and ADC mappings do not yet form one field map

The strongest candidate transmitter uses a q3 **shared-slice** Am2901 map.
Its `D127=B0` phase loop reads the upper Am27S31 bank at `129` and produces
16 distinct `Y129` bytes in 740 reads. The receive-side
[upper-sensitive ADC hypothesis](LOWER-I-D3F8-UPPER-D-ROUTE.md) adds an
independently decoded upper slice. It gives a real `D3F8→3F9→Q` feedback
path, but the transmitter and receiver results have not previously been
shown under one fixed field map.

The [joint screen](joint_tx_rx_mapping_screen.py) keeps that receiver upper
slice fixed and tests all 32 combinations of five disputed *lower* field
groups, including the paired `I7/A0` and `I0/A1` choices. Each choice runs
the real control PROMs twice: 3,000 instructions with held `D127=B0`, Q=0
and the upper ROM bank; and 128 `D3F8` visits with Q=5 and a held ADC byte
`59` versus its low-nibble-only counterpart `09`. The receiver fixture
uses the same inverted-previous-sign condition as the earlier ADC work.

| Fixed-map case | `129` reads / distinct `Y129` values | ADC high nibble changes next `3F9` address? |
| --- | ---: | --- |
| q3 shared-slice transmitter control | 740 / 16 | Not tested as an upper-sensitive map |
| Receiver lower fields, shared slice and no independent upper fields | 740 / 16 | No independent upper ADC path in this control |
| Receiver map with independent upper slice (mask `00`) | 740 / 1 | Yes, 128/128 paired reads |
| One mixed map (mask `0E`) | 740 / 2 | Yes, 128/128 paired reads |

Across all 32 independent-upper-slice variants, 24 complete the 740-read
`129` loop, but none has more than four `Y129` values. Eleven show an ADC
high-nibble effect on the next `3F9` ROM address. Ten do **both**; among
those ten the most varied `Y129` stream has only two values. The saved
[report](results/joint-tx-rx-mapping-screen.json) includes every field
choice, loop count, selected ADC reads, first output bytes and trace digest.

This is a compatibility constraint on the **current hypotheses**. Merely
adding the receiver's independent upper-slice instruction wiring to the
q3 transmitter does not retain the 16-value ROM/Y phase path that supported
the candidate DAC waveform. Switching the disputed lower sources alone
does not explain the collapse: both shared-slice controls retain that path.
The output may use a different high-slice source, a mode-dependent gate, or
a different byte/latch route. The screen uses held inputs and does not score
a full dibit waveform, so it does not rule out all modulation in a two-value
variant. It also does not identify a received bit or physical ADC/DAC net.
Before claiming a single microprogram explanation for C2 and C3, test one
fixed upper-slice/timing map on both the standard dibit replay and independent
ADC streams, with the output and USART routes stated explicitly.
