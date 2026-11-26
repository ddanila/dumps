# Sixteen DSC-recovered characters reach the modeled 8251 and unchanged 8031

The [paced controller TxD test](MAIN-LOOP-USART-TXREADY-17.md) shows
that the 129-bit A4/A5 span used by the DSC line replay is actually
shifted by the modeled 8251. This experiment tests the reverse digital
handoff on the same span. It decodes 64 dibits from the saved **executed
DSC receive states** using the phase map learned only from A4, packs
their 128 bits into 16 bytes, and clocks those bits through an extended
one-byte-buffer 8251 receive model into the unchanged 8031 ROM.

| Selector | Aligned external SYNDET at bit 66 | One-bit-early control | One-bit-late control |
| --- | --- | --- | --- |
| `40` | 16 completed/consumed; 16 exact bytes; zero errors/overruns | 16 consumed, wrong bytes | 15 consumed, wrong bytes |
| `60` | 16 completed/consumed; 16 exact bytes; zero errors/overruns | 16 consumed, wrong bytes | 15 consumed, wrong bytes |

The aligned 16 input bytes equal both the controller-derived TxD span
and the bytes reconstructed from the executed DSC receiver. In each
mode, the 8031's 16 descrambled bytes also match an independent
bit-serial inverse calculation using the same initial history and
selector polynomial. The controller remains in `AF` during this
probe; none of the 16 completed characters overruns the modeled 8251
receive buffer. The two SYNDET controls show that byte alignment is
material.

This closes the **modeled** 16-character reverse serial handoff under
the stated clock and external-sync timing. It does not identify the
physical DSC-to-RxD/RxC/SYNDET circuit or show the 8031 naturally
traversing A3/A4 while it receives this span: the probe starts in
`AF`. The phase map, ADC connection and analog line remain assumed.
C3 and G2 therefore stay open. Next test a photo-compatible circuit
that produces the phase labels and serial bits, and a continuous 8031
state run through the receive transition.

The [machine report](results/joint-mask04-12a-16byte-reverse-handoff.json)
includes the DSC-derived bytes, all three sync timings, unchanged-ROM
controller results, independent descrambler outputs and source hashes.
Reproduce from the microcode directory with:

```sh
python3 g2/joint_mask04_12a_16byte_reverse_handoff.py
```
