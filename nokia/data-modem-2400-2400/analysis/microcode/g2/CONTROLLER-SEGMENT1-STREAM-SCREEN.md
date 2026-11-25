# Scrambled port-01 bytes do not directly contain a 32-symbol reversal run

The [32-symbol PROM replay](PHOTO-SEGMENT1-REPEATED-DIBIT.md) established
what the candidate phase path does when fed repeated `11` dibits. This
[controller screen](controller_segment1_stream_screen.py) checks whether the
bytes actually written to external port 01 during the unchanged 8031's
64-iteration polling-loop replay contain that direct stimulus.

All four executed selector classes provide 54 or 60 port-01 bytes. The screen
groups their bits into contiguous dibits under both serial bit orders and both
possible one-bit symbol alignments, including pairs that cross byte and state
boundaries. The longest run of any identical dibit is **six symbols** (`00`,
`20` and `60`) or **four** (`40`). A fixed swap or inversion of the two
dibit lanes is a bijection, so it cannot turn a shorter run into the 32
identical `11` dibits needed for continuous segment-1 half-turns under this
direct mapping. The original 8031 ROM's port-01 writes were independently
checked against its scrambler in the [long-run replay](MAIN-LOOP-LONG.md).

This rules out **direct contiguous dibit grouping of these recorded
scrambled bytes** as segment 1 in this fixture. The controller's `FF` source
bytes before scrambling, a DSP-side descrambler, a command to generate the
pattern internally, and other controller states remain possible. The
synthetic timer and serial events do not establish a natural operating
sequence or the physical port-01 destination. The [machine report](results/controller-segment1-stream-screen.json)
records all 16 bit-order/alignment cases and source hashes.

The same A4 bytes **do** match the standard's different, scrambled
[segment-2 pattern](CONTROLLER-SEGMENT2-PATTERN.md). That positive match
helps distinguish the two synchronization segments; it does not turn the
scrambled A4 bytes into segment 1.
