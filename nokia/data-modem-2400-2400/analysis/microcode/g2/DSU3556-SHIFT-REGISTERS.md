# Four latched serial-to-parallel registers on the controller board

The unchanged [DSU 3556 front photograph](../../../photos/PXL_20261123_114723348.jpg)
shows four packages clearly marked `CD4094BE`, at the four coordinates in the
[reproducible crop](photo_shift_registers.py). The [contact sheet](results/dsu3556-cd4094.jpg)
preserves their markings and photo positions. The raw photograph is unchanged.
[TI's CD4094B datasheet](https://www.ti.com/lit/ds/symlink/cd4094b.pdf)
describes each as an eight-stage serial shift register with a storage latch
and eight buffered parallel outputs. Four devices therefore have **32 parallel
output stages**, the same capacity as the 8031's executed four-byte mode-0
send. The executed [interface study](../../controller/INTERFACE.md) also
observes a P1.2 latch pulse only after the fourth transmission completes.

This is a **hardware-compatible explanation** of the four-byte transaction:
the 8031 may clock 32 bits into these registers and strobe their parallel
outputs together. The photograph does not prove that the four devices are
cascaded, that P1.2 drives their strobe pins, the bit order, or where each
parallel output goes. Some outputs may serve local indicators or control
logic; a DSC2847 connection is still a separate hypothesis.

The [earlier bridge](RECEIVED-CHAIN-MICROCODE.md) offered each outgoing byte
to D38E on successive DSC loop visits. If the four CD4094 devices hold a
parallel control word, a more direct candidate is to hold a selected output
byte or bit stable between controller latch events. The
[latched-frame screen](PHOTO-LATCHED-FRAME.md) executes that alternative.
Neither candidate is promoted to board wiring without a pin-level trace.
The [four-chip order model](PHOTO-CD4094-ORDER.md) now shows that a
LSB-first four-byte send would reverse the byte order across a simple
cascade, and can reverse each byte depending on Q-pin-to-D-bus order.
That distinction changes which q3 phase-loop branch a held frame can select.
