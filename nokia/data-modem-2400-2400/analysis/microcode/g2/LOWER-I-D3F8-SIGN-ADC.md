# Inverted-sign condition keeps the candidate ADC loop active across symbol streams

The previous [ADC decoder screen](LOWER-I-D3F8-ADC-DECODER.md) found
input-sensitive history at `D3F8`, but its inverted-previous-zero condition
eventually returned through `3EE` and repeated at `1E9/1EA`. The raw PROM
word at the `3ED` and `1EA` branch tests is identical, so a condition
hypothesis must apply to both words. The [select-0 screen](lower_i_d3f8_condition0_screen.py)
tests zero, carry, sign and overflow, each with both flag timings and
polarities, against two 32-sample complementary ADC streams. It keeps the
same PROM-data mapping, Q=5 and `03/05` D3F8 decoder driven by ADC bit 0.

Only **inverted sign**, with either previous- or current-flag timing, keeps
*both* tested patterns in D3F8 for all 6,000 visits. Inverted previous zero
keeps the original `0,1,3,2` pattern but loses steady `0,0,0,0`. The
[32-case condition report](results/lower-i-d3f8-condition0-screen.json)
records the D3F8, `3EE`, `1E9/1EA`, `1EB` and `1EC` counts for every policy;
the condition-mux source, polarity and clock phase remain untraced.

The [long sign-condition runner](lower_i_d3f8_sign_adc.py) then tests six
distinct repeated four-dibit patterns, with **128 consecutive ADC samples**
each. For each of the two flag timings, all six runs:

- reach all **24,000** scheduled D3F8 input visits and end at `3F8`;
- offer the 24,000-byte sequence and make **48,003** selected ROM reads;
- never enter `1E9` or `1EA` during the 192,047-microinstruction window.

The independent reference receiver recovers the known dibits of each
stimulus. Each pattern has a distinct real-PROM trace digest under a fixed
timing. The [saved report](results/lower-i-d3f8-sign-adc.json) contains the
per-pattern counts, digests and source hashes.

A detailed 32-sample comparison checks actual input selection. For the
`0,1,3,2` and `0,0,0,0` patterns, both with the same `03/05` decoder, every
one of 6,000 offered D3F8 bytes is selected by the ALU. The PC paths are
identical. Yet the modeled RAM/Q/ALU/next-PC/stack snapshots differ at
**5,259** D3F8 visits, selected ROM addresses differ at **10,072** read
events, and ALU Y differs at **5,031 / 5,034 / 4,952** visits of
`3F8 / 3F9 / 3FA`. Both timing alternatives give those counts. Thus this
candidate can sustain multiple distinct waveforms and retain input-dependent
internal computation; the different traces are not just early exits.

This is a **conditional** receive-side explanation only. The ADC bit
decoder, D0 bias, PROM-to-Am2901 mapping, oscillator division and condition
source are assumed. The detailed selected-byte check covers two short
streams; the long runs count offered visits without saving full traces.
No symbol or bit decision, output latch or route to USART-01 RxD is
identified, so C3 remains open. The next test should inspect the sustained
loop's register, ROM-address and ALU-Y events at symbol timing, look for a
decision that tracks known dibits across patterns and phases, and test its
candidate route to the controller.
