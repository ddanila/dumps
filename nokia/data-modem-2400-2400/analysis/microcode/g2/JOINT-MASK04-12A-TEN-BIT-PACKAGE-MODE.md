# Ten-bit package gate: held-81 transfer and failure

The matched mode-boundary test rejected the frozen nine-bit phase gate. We
therefore tested a ten-bit candidate that retains the earlier nine bits and
captures `3F8` Y6 at visit `94`. U14/U12/U3 have enough candidate storage for
this schedule, and the observed row-0 Y0/Y1 values remain stable from visits
`46` to `47`. These are assumed nets and latch clocks, not identified Nokia
connections.

The first U13/U15/U19/U21 gate fits 54 states in 58 development streams, but
fails four fresh held-`81` real-PROM/controller cases at carrier starts
`169/171`: 12/7 and 16/10 wrong dibits, wrong modeled line bytes and wrong
executed controller payloads, with no modeled ADC clipping. The expanded
56-state graph has no conflicts. Of its two new states, `135` is predicted
correctly; `32C` needs relative phase 2 but the frozen gate assigns 1. Every
wrong transition touches `32C`. The [failure audit](results/joint-mask04-12a-ten-bit-mode81-audit.json)
contains the source-hashed captures and graph.

Reallocating the four U15 input arms and one U19 term yields a revised gate
within the same photographed package counts: U12 three flip-flops, U14 four
latches, U3 three latches, U13 five inverters, U15 one 4-2-3-2 AOI, U19 three
NAND3 gates and U21 three NOR2 gates. It fits all 56 states and 62 development
streams with zero staged-state or dibit errors. That fit includes the failed
`169/171` streams; it is not independent validation. The exact equations and
source hashes are in the [revised route report](results/joint-mask04-12a-ten-bit-package-route2.json).

We froze that revision before fresh carrier-`173/175` payloads, using held
`81` at every assumed `3EB` read. Both selectors at `173` recover all 64
dibits, exact modeled line bytes and exact executed controller payloads,
including unseen states `181` and `31C`. Both selectors at `175` miss 12/64
dibits and deliver wrong line/controller bytes, despite zero clipped samples
and zero USART status errors. They visit unseen `12D` and `136`; only `12D`
is mispredicted. Every wrong transition touches `12D`. The joined 66-stream
graph has 60 states, zero conflicts, and two components of 40 and 20 states.
Its inferred relative phase for `12D` is 2, while the frozen gate assigns 1.
The [holdout](results/joint-mask04-12a-ten-bit-package-route2-mode81-holdout.json)
and [audit](results/joint-mask04-12a-ten-bit-package-route2-audit.json)
record the independent run and classification.

This is a real unseen-state gate failure, not a failure to look up a state.
The observed labels admit a three-literal product for `12D` (`s3 & s5 & s8`)
without covering any observed phase-bit-0 off state. It cannot simply be
appended to an already occupied U15. Next search for a package-budgeted
reallocation or another photo-compatible capture route, freeze it, and test
fresh real-PROM/controller data. Keep C3 and G2 active. The two disconnected
phase components leave their relative offset unconstrained, and no actual
latch, gate, analog or USART net has been traced.
