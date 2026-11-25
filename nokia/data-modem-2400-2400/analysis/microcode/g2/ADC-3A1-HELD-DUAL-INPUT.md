# Held D3A1 ADC samples do not retain receive history with D38E line bits

The prior [dual-input impulse screen](DUAL-INPUT-ADC-NIBBLE.md) found that a
byte at `D3A1` can change R7 for one loop boundary while controller bits
remain at `D38E`. This [follow-up](adc_3a1_held_dual_input.py) tests a
continuous, conversion-paced signal under the same two candidate U2 I2
sources, U11.0 and U11.4. It keeps the unchanged 8031 ROM's port-01 bits
present at D38E instead of replacing them with ADC data.

With the assumed 14.4 MHz microinstruction clock, the reached loop visits
each input site every 12 instructions. At 9,600 ADC samples/s, each
complementary code `127 − reference PCM` is therefore held for 125 site
visits. At 2,400 line bits/s, each real controller bit is held for 500
visits. The five line bits used here are `0 0 0 1 1`, taken LSB-first from
the B4 port-01 stream. The reference modem generates a decodable waveform;
two ADC sequences reverse the first 16 sample codes and share their final
four samples. These bus routes, code range, clock divisor and alignment are
still hypotheses.

For each U11 source, both real-PROM executions complete 30,044
microinstructions and select all **2,500** offered ADC bytes and **2,500**
offered controller-bit values. The distinct ADC histories change the modeled
state during their different samples. At the first shared ADC sample,
boundary 2,000, the full modeled RAM/Q/ALU/stack state converges and remains
equal. The 5,000 reached candidate output ALU events and three selected ROM
addresses are identical between histories for both mappings; final states
also match.

This closes a held-sample receive-history interpretation of these two
`D3A1` fixtures. It does not rule out another ADC bus phase, latch, field
mapping or program path. No recovered bit reaches the USART-01 receive side,
so C3 remains open. The next receiver search should prioritize a path that
retains a conversion-dependent value across a later sample, ideally while
the controller stream continues. The [machine report](results/adc-3a1-held-dual-input.json)
records both schedules, sample codes, selected-input counts, state comparison
and source hashes.
