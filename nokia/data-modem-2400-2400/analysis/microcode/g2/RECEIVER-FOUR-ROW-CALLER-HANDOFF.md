# Third-row release carries ADC state into the caller; fourth-row release erases it

The sustained [four-row receive fixture](RECEIVER-FOUR-ROW-CONDITION.md)
reaches the `3EA` wrapper through the real reset and `18C` caller chain.
Its assumed TEST source keeps `3ED` looping. This experiment substitutes a
labelled external 1→0 TEST event at `3ED` after 1,500 selected ADC bytes,
then follows the executed return through `3EE→18D` to the terminal `084`
word. The event is a timing hypothesis; no board TEST wire is claimed.

Five 32-sample reference inputs use constant dibits 0, 1, 2 and 3, plus
the cyclic `0,1,3,2` pattern. Their complementary ADC bytes are held for 47/46 table
visits per sample under the same joint upper-source mask-08 field map and
counter-like `0→1→2→3` dispatch. Two release phases are compared:

| Release at `3ED` | First `084` cycle | Distinct RAM/Q states at release | Distinct RAM/Q states at `084` | PC paths |
| --- | ---: | ---: | ---: | ---: |
| After ADC-sensitive `3F7–3FA` row, cycle 48,034 | 48,191 | 5/5 | 3/5 | 1/5 |
| After following `3FB–3FE` row, cycle 48,042 | 48,199 | 1/5 | 1/5 | 1/5 |

At the third-row release, R11, R12 and Q vary with input. The caller retains
some of that difference: its terminal RAM state takes three values across
the five patterns. After the fourth row, the complete modeled RAM/Q state
is identical across all five at release and remains identical at `084`.
Every run selects all 1,500 offered ADC bytes, returns to the same `18D`
caller, and reaches `084` cleanly.

The sole difference in the executed control records after third-row release
is TEST at `1AA` for the repeated `22` input: 1 instead of 0. `1AA` is an
`INC` instruction, so both values advance to `1AB`; the PC path is identical
for all inputs. There is no observed input-dependent branch, dibit decision
or USART-01 RxD transition on this route. A latch sampling before the fourth
row or another mode-dependent output could still use the transient state.
This narrows the **timing** that such a route would require, without treating
the untraced gate as a blocker or claiming C3.

The [machine report](results/receiver-four-row-caller-handoff.json) saves
each trace digest, every post-release PC/TEST tuple through `084`, checkpoint
RAM/Q state, and source hashes. Reproduce with
`python3 g2/receiver_four_row_caller_handoff.py` from the microcode directory.
