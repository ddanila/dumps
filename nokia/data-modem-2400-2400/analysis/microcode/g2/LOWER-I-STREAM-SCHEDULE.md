# D3F8 stream timing does not sustain the tested controller or forward ADC input

The [D3F8 input screen](LOWER-I-D3F8-INPUT.md) found retained effects but an
early branch when real 8031 bits were offered one per loop visit. The
[schedule screen](lower_i_stream_schedule.py) tests whether bit hold time,
initial Q or sample alignment rescues that candidate. It retains the same
real-PROM mapping: I7/A0 from inverted U10 D6, I0/A1 from U11 D2 and lower
I6 from U11 D0. Those latch/data routes and the D3F8 source remain untraced.

The controller fixture supplies the 128 bits produced by executing the 8031
scrambler. Each D3F8 byte keeps D0 high and puts the bit on D1, D2 or D3.
For one visit per bit, the screen runs **all 256 initial Q values** for each
lane. Visit counts, selected-ROM counts and final PCs repeat by Q low nibble;
no Q seed consumes all 128 offered bits. Holding each bit for 2, 4, 8 or 16
visits is tested for Q=`00–0F`; none consumes the corresponding 256, 512,
1,024 or 2,048 site values.

| D lane | Most visits, one per bit (all Q) | Hold 2 | Hold 4 | Hold 8 | Hold 16 |
| --- | ---: | ---: | ---: | ---: | ---: |
| D1 | 28 | 49 | 43 | 53 | 105 |
| D2 | 38 | 50 | 32 | 56 | 104 |
| D3 | 118 | 100 | 39 | 51 | 99 |

The ADC-like control uses 128 samples from the validated V.26 ter reference
transmitter, encoded as `127−sample` or complementary `128+sample`. At Q=5,
none of the **128 cyclic start positions** of the forward stream reaches all
128 D3F8 visits: maxima are 121 and 98, respectively. One deliberately
time-reversed `127−sample` fixture reaches 133 visits. Reversal is an
ordering diagnostic, not a physical receive sequence or a recovered-bit
witness. Q=9 and both polarities/orders are also recorded in the report.

The [machine report](results/lower-i-stream-schedule.json) saves verified
Q-class summaries, every held-schedule visit count, the ADC shift screen,
trace digests for the saved cases and source hashes.
These bounded negatives narrow this particular D3F8 wiring and timing
family; they do not exclude another byte polarity, sample clock, startup
state for held inputs, instruction mapping, or receive ingress. No DAC-bound
samples or decoded bits have been identified.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/lower_i_stream_schedule.py
```
