# No direct symbol-bit decision at the tested D3F8 state sites

The [inverted-sign ADC loop](LOWER-I-D3F8-SIGN-ADC.md) runs for 128 samples
under six different dibit patterns and changes internal state with input.
The [symbol-bit screen](lower_i_d3f8_symbol_bit_screen.py) asks whether a
simple fixed bit of that state already represents either transmitted dibit
bit. It executes the real PROMs with inverted **previous sign** on condition
select 0, the same Q=5 and `03/05` D3F8 input decoder, and the same six
128-sample reference streams. During each run, every D3F8 byte is checked
against the offered sequence and confirmed selected by the ALU.

Each symbol spans **1,500 D3F8 visits** under the assumed clock. For each
symbol, the screen saves Y at `3F8`, `3F9` and `3FA`, Q, and all 16 RAM bytes
after `3FA`. It tests every bit of these **20 channels**, every one of the
1,500 fixed visit phases, both bit polarities and symbol offsets from −2 to
+2. Symbols 2–13 of each 16-symbol window provide 36 training checks from
three patterns and 36 holdout checks from three other patterns. A candidate
must use one channel, bit, phase, polarity and lag across all patterns.

| Target dibit bit | Fewest training errors / 36 | Exact training fits | Best selected low-training candidate: training / holdout errors |
| --- | ---: | ---: | ---: |
| 0 | 1 | 0 | 3 / 13 |
| 1 | 3 | 0 | 4 / 15 |

The [saved report](results/lower-i-d3f8-symbol-bit-screen.json) records the
candidate details, trace digests, fixture and source hashes. The best
holdout figures above are among candidates with at most four training
errors; they are not evidence of a decoded bit. Even the training patterns
have no exact direct-bit fit in this search. At one simple end-of-symbol
snapshot, Y at `3F8` repeats with the source pattern but gives the same
`F8` value for two different dibits, illustrating why input sensitivity
alone cannot establish a four-way decision.

This excludes only a **fixed, direct or inverted bit** of the tested state
sites under one timing and field/input mapping. It does not test a
differential decision between symbols, a two-bit or multiword code, a
different output site or a separately clocked latch. The ADC route and
condition wiring remain assumptions, and no USART-01 RxD transition is
observed. The next receive test should look for a **symbol-to-symbol state
change or decoded two-bit value** that generalizes to independent symbol
sequences, then check whether any corresponding signal can reach RxD.
