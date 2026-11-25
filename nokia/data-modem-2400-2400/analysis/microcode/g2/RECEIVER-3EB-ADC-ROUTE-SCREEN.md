# ADC bus hold at the receive wrapper changes control flow

The sustained alternating `3EF/3F7` fixture supplies complementary ADC
bytes at `3F8` only. Its wrapper word `3EB` also selects external D in the
current joint field mapping, so a direct ADC bus held through both words is
a separate photo-compatible hypothesis. The
[route screen](receiver_3eb_adc_route_screen.py) executes the real PROMs under
the same 0/2 dispatch schedule, Q/RAM seed and previous-sign condition. It
offers each ADC sample at both of the `3EB` visits per `3F8` visit, aligning
the hold to the 94/93-visit converter schedule.

| `3EB` input | `3F8` input | `3F8` visits in 48,047 instructions | Final PC |
| --- | --- | ---: | --- |
| Default `01` | 32-sample reference waveform | 3,000 | `3F0` |
| Reference waveform | Held `09` | 282 | `084` |
| Reference waveform | Same waveform | 282 | `084` |

The reference waveform begins `00,59,D7,BE,40,36,BD,F6` as complementary
codes. The two `3EB`-fed cases each make 565 `3EB` visits, then leave the
receive loop. The same outcome with or without changing `3F8` input
localizes this exit to the alternate wrapper feed under this fixture.

Held-byte controls make the dependence clear: `00`, `01`, `09`, `19` and
`59` at `3EB` preserve all 3,000 `3F8` visits; held `A9` or `FF` reaches
`084` after its first `3EB` read, before any `3F8` visit. Thus the presently
modeled wrapper cannot simply see all complementary ADC bits continuously
while sustaining the tested receive waveform. The result does **not** rule
out a separately enabled ADC buffer, a different bit mapping, condition
source, clock phase or dispatch source. It does not identify a receiver bit
or USART RxD route.

The first-branch trace identifies the immediate divergence. Held `09` gives
Y=`0x10` at `3EB` and the first `3ED` test returns to `3EA`; held `A9` gives
Y=`0xB0` and that test proceeds to `3EE`. The program's own loop decision,
not a trace-parser threshold, causes the early exit.

The [machine report](results/receiver-3eb-adc-route-screen.json) includes
all cases, read counts, trace digests and the script hash. Reproduce with
`python3 g2/receiver_3eb_adc_route_screen.py` from the microcode directory.
The next discriminating fixture should vary the `3EB` bus enable or lane mask
explicitly while preserving the real `3F8` samples, and inspect whether a
new decision or output state appears. No untraced net is a goal blocker.
