# The receive loop carries one ADC pulse briefly into the next visit

The [matched-tail impulse capture](JOINT-MASK04-RECEIVE-IMPULSE-MEMORY.md)
found no difference at its selected state/output capture points after a
one-sample ADC pulse. This [full-trace comparison](joint_mask04_receive_pulse_carryover.py)
checks every executed word, register write, flag, TEST level, ROM read,
Q and Y in the same varying-waveform baseline and sample-25 `51→B1`
pulse runs. Both execute **96,047 real-PROM words** and **3,000 ADC
visits** with identical PC paths and final emulator state. Their saved
full-trace digests match the earlier impulse report.

The last altered-sample row-3 `3FE` occurs at cycle 39,049. The next
ADC sample is already identical in both streams, but it is not selected
at `3F8` until cycle 39,071. Between those points the preceding sample
still affects the first row's arithmetic:

| Interval | Different ALU rows | Different Q rows | Different register-write events | Different ROM reads | Different TEST levels |
| --- | ---: | ---: | ---: | ---: | ---: |
| 21 cycles before next `3F8` read, 39,050–39,070 | 14 | 6 | 15 | 4 | 2 |
| From next `3F8` read onward | 0 | 0 | 1 | 0 | 0 |

At cycle 39,050, `3ED` Y is `00` versus `F2`; the following `3EA`
selects different real-ROM addresses and its TEST level differs, but
the program path does not branch. Q rejoins by cycle 39,056; flags
rejoin by 39,062. The modeled RAM still differs just before the next
`3F8` read and for two cycles after it. A differing write event at
`3F9` changes no Y or Q; the entire modeled state and trace rejoin at
cycle **39,073**, the next `3FA`. No later field or state difference
appears through the end of either run.

This corrects an overbroad reading of the earlier capture: the tested
loop has **short-lived previous-sample history** in intermediate row
outputs before the current ADC byte is selected. Its selected post-visit
captures still show no persistent state, and the history does not
survive the first current-input `3FA` word. A photo-compatible latch
clocked during that prefix could observe the old sample; no such
connection or received-bit decision is established. The mapping,
ADC route, TEST source and dispatch timing remain assumptions. C3 and
G2 remain open and active.

Run `python3 g2/joint_mask04_receive_pulse_carryover.py` from the
microcode directory. The [machine report](results/joint-mask04-receive-pulse-carryover.json)
contains the complete difference counts by word, carryover rows,
source hashes and convergence cycle.
