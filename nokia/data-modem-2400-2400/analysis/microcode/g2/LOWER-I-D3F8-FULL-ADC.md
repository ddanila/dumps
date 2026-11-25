# Full ADC sample bytes sustain the candidate D3F8 loop

The photographed ADC0800 exposes a complementary **8-bit** sample bus. The
earlier [inverted-sign loop](LOWER-I-D3F8-SIGN-ADC.md) used only one ADC bit
to choose between diagnostic D3F8 bytes `03/05`. The
[full-byte experiment](lower_i_d3f8_full_adc.py) now holds each entire
reference sample byte for alternating **188/187 D3F8 visits**. It uses the
same real four-PROM image, candidate Am2901 field mapping, Q=5 and inverted
previous-sign condition select 0. The ADC-to-D3F8 connection, converter
range and microinstruction clock remain assumptions.

For six repeated four-dibit patterns, the experiment compares raw
complementary codes `127−PCM`, natural-binary controls `128+PCM`, and
D0-forced-high versions of both codings for two patterns. The independent
reference receiver recovers each stimulus. All **16** cases reach the full
**24,000 D3F8 visits** for 128 samples, make **48,003 selected ROM reads**,
avoid `1E9/1EA` and end at `3F8`. The raw complementary streams contain
**48–81 samples with D0 low** per 128-sample window. Thus a forced D0-high
bias is **not required to sustain this particular sign-condition fixture**;
this says nothing about the board's untraced bus wiring.

Four separately seeded **nonperiodic** 16-dibit streams give the same
24,000-visit result with raw complementary bytes. Their reference decisions
also have zero errors. These controls reduce the chance that a repeated
four-symbol pattern alone explains the sustained loop. The
[saved report](results/lower-i-d3f8-full-adc.json) records every pattern,
seed, code count, D0-low count, visit count, trace digest and source hash.

Detailed 32-sample traces check what those visits mean. For `0,1,3,2` and
steady `0,0,0,0`, **all 6,000 offered full ADC bytes are selected by the
ALU** and the PC paths match. Their RAM/Q/ALU/next-PC/stack snapshots differ
at **5,812** D3F8 visits, selected ROM addresses at **11,046** events, and
Y at `3F8/3F9/3FA` at **5,408/5,389/5,390** visits. Holding the same
`0,1,3,2` waveform but reducing each full byte to its bit-0 `03/05`
projection changes all 6,000 state boundaries, 11,179 selected ROM
addresses and thousands of Y events on the same PC path. This comparison
shows that the candidate uses more than the chosen one-bit projection, but
does not isolate which additional input bits matter.

An explicit masking control supplies the **same low nibble** of each raw
complementary code with its high nibble forced to zero. For **both** detailed
patterns, that produces the **identical complete trace digest**, all 6,000
state boundaries, all selected ROM addresses and all three Y streams. The
modeled computation therefore has **no observed sensitivity to ADC bits
4–7** under this field mapping. It consumes at most the low nibble of the
offered 8-bit sample in these witnesses. The bit-0 projection changes other
low-nibble bits as well, explaining why it differs from the raw code.

This is a sustained, amplitude-dependent receive-input *candidate*, but it
does not identify an 8-bit demodulator. The physical ADC/buffer/DSC route,
input bit order,
reference range, conversion clock, condition source and PROM-to-Am2901
connections are untraced. The exact-byte selection check covers two short
streams; the long runs count offered visits without saving full traces. No
recovered bit or USART-01 RxD event has been found. The next test should
check whether another photo-compatible field or latch route makes the
upper ADC bits observable, and search the sustained low-nibble computation
for a symbol decision that generalizes to nonperiodic streams.
