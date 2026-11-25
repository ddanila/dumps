# Changing the mask-04 TEST flag does not reveal a receive branch

The [joint mask-04 mapping](JOINT-FOUR-ROW-RETENTION-TX.md) retains
ADC-dependent state through all four receive rows, but its assumed
inverted previous-overflow TEST gives no input-dependent conditional
branch. This screen checks nearby, labelled TEST pin alternatives under
that same fixed field map. The physical TEST wiring is untraced.

A held `09` ADC code runs for 48,047 real-PROM instructions under all 16
combinations of previous/current ALU flag timing, zero/sign/carry/overflow
source and polarity. Exactly three choices select all 1,500 ADC bytes at
`3F8` and complete the fourth row 1,500 times:

| Timing | TEST source/polarity |
| --- | --- |
| Previous ALU flags | inverted sign |
| Previous ALU flags | inverted carry |
| Previous ALU flags | inverted overflow |

Each survivor then runs both a changing `0,1,3,2` reference waveform and
an all-zero-dibit control for 48,047 instructions apiece. All six runs
select 1,500 complementary ADC bytes, take the same PC path between the
paired waveforms and retain different complete RAM/Q state after `3FE`
on **1,312/1,500** visits. Thus changing the TEST flag within this
surviving family does not lose the state retention.

| TEST source | Changed TEST at `3EA` | Changed TEST at `3EC`/`3ED` | Changed TEST at any reached conditional command |
| --- | ---: | ---: | ---: |
| Inverted previous sign | 282 | 0/0 | 0 |
| Inverted previous carry | 234 | 0/0 | 0 |
| Inverted previous overflow | 234 | 0/0 | 0 |

`3EA` executes PLP (`5`), which does not branch on TEST. `3EC` executes
conditional BSR (`4`) and `3ED` conditional BLT (`2`); their TEST values
and next PCs do not differ between the paired inputs. The audit also
checks every other reached conditional command, including startup, and
finds no TEST or next-PC difference. Under these three fixtures the
ADC-dependent state is not converted into a branch decision.

This excludes only the tested pin timing/source choices and waveforms,
not another field map, input gate, mode, or external output latch. No
bit reaches USART 01 RxD, so C3 remains open. The next experiment should
follow a photo-compatible output consumer or alter the input/field route,
instead of repeatedly substituting these three TEST flags.

The [machine report](results/receiver-mask04-flag-condition-screen.json)
records all 16 held-input runs, per-site conditional comparisons, trace
digests and source hashes. Reproduce with
`python3 g2/receiver_mask04_flag_condition_screen.py` from the microcode
directory.
