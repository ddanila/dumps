# A conditional joint transmitter and ADC instruction map

The earlier [joint field screen](JOINT-TX-RX-MAPPING.md) held the receiver's
upper-slice instruction sources fixed. Its ADC-sensitive variants retained
at most two `Y129` values in the held transmitter loop. The
[new screen](joint_upper_source_screen.py) instead tests one small,
untraced upper-instruction alternative: U8 I0 and I7 both take inverted
U17 D5. The other U8 instruction sources start from the q3 transmitter
map, with the photographed *candidate* I4/I6 crosslinks applied by the
split-slice scenario. U8 B uses the lower-slice B address. All four real
control PROMs and the real Am27S31 table are executed.

Five of 32 lower-field combinations (`04`, `06`, `08`, `0A`, `0E`) retain
both 16 distinct `Y129` bytes and 16 distinct upper-bank ROM addresses in
740 held `D127=B0` transmitter reads, while completing 6,000 `D3F8`
visits on a changing reference ADC stream. The selected [mask `08`
mapping](results/joint-upper-source-mask08-mapping.json) uses the receiver
lower fields except I2, which uses q3's source.

For mask `08`, held complementary ADC `59` versus `09` changes the next
`3F9` ROM address on all 128 paired visits. On a 32-sample reference stream,
all 6,000 ADC bytes are selected in both full-byte and high-nibble-masked
runs. Their PC paths match, while 5,625 state boundaries and 5,624 of
18,007 selected ROM addresses differ. Two 128-sample periodic streams and
one seeded nonperiodic stream each remain in the real-PROM `D3F8` loop for
24,000 visits. The two periodic masked controls also complete. Exact
fixtures, digests and source hashes are in the [saved report](results/joint-upper-source-screen.json).

This removes the *local* compatibility conflict between a changing held
transmitter ROM path and sustained ADC-sensitive execution. It does not
establish that U17 D5 drives either U8 pin, that the inverted level is
latched at the assumed phase, or that the two candidate slice crosslinks
are continuous. The transmitter still needs a controller-driven dibit run
with a specified DAC latch and output bus. The receiver still needs a
decision that generalizes to independent streams and a path to USART RxD;
the present address differences do not identify a recovered bit or echo
cancellation. The transmit and receive scenarios also use different,
explicitly labelled diagnostic input levels and startup states. Test their
physical plausibility before treating this map as a Nokia board model.

Reproduce with:

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/joint_upper_source_screen.py
```
