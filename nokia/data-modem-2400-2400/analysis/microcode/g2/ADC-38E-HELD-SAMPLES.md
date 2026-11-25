# Held ADC samples still do not give the D38E route receive history

The earlier [ADC sample run](ADC-SAMPLE-RUN.md) offered a new byte at every
`38E` visit. In that fixture the visit recurs every 12 microinstructions,
which at the assumed 14.4 MHz microinstruction clock is far faster than a
9,600-sample/s ADC schedule. This [follow-up](adc_38e_held_samples.py) holds
each complementary ADC0800 candidate byte for **125 visits**, or 1,500
microinstructions per sample. The conversion range, clock divisor and physical
bus remain assumptions. The photographed ADC0800's latched outputs make a
held sample more plausible than a byte changing on every instruction group.

An independent V.26-class reference transmitter supplies a decodable sample
stream. Two sequences use the same 20 sample codes but reverse the first 16;
their last four codes are identical. Each run executes 30,044 DSC
microinstructions cleanly under the existing q3, Q=5 D38E candidate, with
2,500 selected D-input visits and matching four-word dispatch groups. The
first 2,000 post-group modeled states differ between the histories. At the
**first shared input group**, index 2,000, the full modeled RAM/Q/flags/stack
states become identical and remain so through the final 500 groups. The
final modeled states match, and neither run has a selected Am27S31 read after
the first dispatch.

Thus this route responds to the current conversion byte but does not retain
the earlier waveform under the tested mapping and timing. This is a scoped
negative receiver result, not evidence against the ADC0800 itself. No
demodulated bit reaches USART-01. The next C3 experiment should test a
separate ADC ingress or a jointly changed instruction/address and latch
schedule, with the controller command and line-bit sources present at the
same time. The [machine report](results/adc-38e-held-samples.json) records
the sample codes, scheduling assumptions, state comparison and source hashes.
