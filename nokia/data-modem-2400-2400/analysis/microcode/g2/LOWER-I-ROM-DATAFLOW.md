# The 3F7 quarter-sine read writes R10 but does not reach another output

The [alternate lower-instruction loop](LOWER-I-BRANCH-FOLLOWUP.md) reads eight
addresses of the Am27S31 upper bank at `3F7`. The
[dataflow experiment](lower_i_rom_dataflow.py) asks whether the selected bytes
affect anything beyond that read under U2 I6←U11.0, Q=5 and zero initial RAM.
It runs 1,580 real-PROM microinstructions and changes only the assumed A8 bank
at `3F7`, leaving other ROM sites at their prior bank. The A8 source and
U11-to-U2 pin assignment are not traced board facts.

All **192** `3F7` visits select a ROM byte in both runs. The bank change
changes R10 repeatedly and leaves a different final R10 (`04` versus `05`).
Across the complete paired traces, **R10 is the only RAM location that ever
differs**. The ALU's internal F differs at each `3F7` read, but ALU Y, carry,
zero/sign/overflow flags, Q, stack and PC path do not differ at any cycle.
This is a real ROM-dependent register write in the modeled path, but it has
no observed downstream sample or branch effect.

To isolate one ROM byte, the experiment replays all selected `3F7` bytes
through a PC-keyed D sequence. The replay exactly reproduces the original
trace digest and full modeled state. Replacing only byte 20 (`49`→`65` hex)
changes its R10 checkpoint; the next `3F7` checkpoint and every later one
match the replay control. No ALU Y or PC value changes at any cycle. Thus a
continuously different bank can keep R10 different, while a single table-byte
impulse is erased by the next loop iteration.

The [machine report](results/lower-i-rom-dataflow.json) records both byte
streams, the isolated change, full-trace comparisons, digests and source
hashes. The quarter-sine address pattern is an arithmetic lead, not a
demonstrated carrier or DAC-bound sample stream. A useful next candidate must
connect this ROM-dependent state to a later register read or output latch,
or use a different instruction/timing path; pin uncertainty does not block
trying it.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/lower_i_rom_dataflow.py
```
